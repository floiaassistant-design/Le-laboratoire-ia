"""EXP-017: narrow, abstaining input-only router and reproducible audit.

No language model, answer scorer or network is called here. Grammar coverage
is intentionally limited; 'needs_review' is a REQUEST for a role, not proof
that an independent agent improves correctness.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass, replace
import hashlib
import json
from pathlib import Path
import re

from .exp010a_adaptive import choose
from .exp011_manual import task_profile
from .exp014_neutral_padding import planned_calls, NUMBER
from .exp015_content_router import candidate_route
from .exp016_routing_stress import load_frozen_manifest as load_exp016

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "experiments" / "exp017-cases.json"
FROZEN_BLOB = "c834f0b9360c93eb930b5045621fba98a9d4ce43"
CATEGORIES = ("explicit_digits", "explicit_words", "explicit_two_stage", "ambiguous_or_nonmath")
VARIANTS = ("base", "tagged_neutral", "tagged_format")
POLICIES = ("baseline_length", "candidate_content", "candidate_conservative")
STATES = ("single", "parallel", "review", "needs_review", "uncertain",
          "unsupported", "blocked", "blocked_by_budget", "invalid_input")
NOTE_NEUTRAL = "Non-mathematical note: no extra numbers are given."
NOTE_FORMAT = "Formatting instruction: include the word then in the margin."
WORD_VALUES = (
    "zero one two three four five six seven eight nine ten eleven twelve "
    "thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty "
    "thirty forty fifty sixty seventy eighty ninety"
).split()
ATOM = r"(?:\d+(?:\.\d+)?|" + "|".join(WORD_VALUES) + r")"
BINARY_OP = r"(?:plus|minus|times|divided\s+by)"
SECOND_OP = r"(?:add|subtract|multiply\s+by|divide\s+by)"
GRAMMAR = re.compile(
    rf"(?:compute|calculate)\s+({ATOM})\s+{BINARY_OP}\s+({ATOM})"
    rf"(?:,\s*(?:then|afterward|next)\s+{SECOND_OP}\s+({ATOM}))?"
    rf"\s*[.!?]?\Z", re.IGNORECASE
)
MATH_CUE = re.compile(
    r"\b(?:compute|calculate|how many|what is|total|remaining|remain|left|sum|difference|product)\b",
    re.IGNORECASE,
)
WORD_TOKEN = re.compile(r"\b(?:" + "|".join(WORD_VALUES) + r")\b", re.IGNORECASE)
NOTE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=(?:Non-mathematical note:|Formatting instruction:))", re.I)
NOTE_PREFIX = ("Non-mathematical note:", "Formatting instruction:")
EXACT_MANIFEST = {"experiment", "phase", "status", "model_calls", "answers_included",
                  "tagged_neutral", "tagged_format", "cases"}
CASE_KEYS = {"id", "category", "question"}


@dataclass(frozen=True)
class Decision:
    status: str
    calls_planned: int
    reason: str
    annotation_count: int


def git_blob(payload: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(payload)).encode() + b"\x00" + payload).hexdigest()


def load_manifest(path: Path = MANIFEST) -> dict:
    payload = path.read_bytes()
    if git_blob(payload) != FROZEN_BLOB:
        raise ValueError("EXP-017 frozen manifest SHA mismatch")
    data = json.loads(payload.decode("utf-8"))
    validate_manifest(data)
    return data


def validate_manifest(data: dict) -> None:
    if not isinstance(data, dict) or set(data) != EXACT_MANIFEST:
        raise ValueError("Invalid EXP-017 manifest structure")
    if (data["experiment"] != "EXP-017"
            or data["phase"] != "frozen_author_constructed_inputs_before_candidate_execution"
            or data["status"] != "question_only_no_model_results"
            or data["model_calls"] != 0 or data["answers_included"] is not False
            or data["tagged_neutral"] != NOTE_NEUTRAL
            or data["tagged_format"] != NOTE_FORMAT):
        raise ValueError("EXP-017 preregistration altered")
    cases = data["cases"]
    if not isinstance(cases, list) or len(cases) != 16:
        raise ValueError("Exactly sixteen cases required")
    expected_ids = [prefix + "-" + str(n).zfill(2)
                    for prefix in ("d", "w", "m", "a") for n in range(1, 5)]
    if [c.get("id") for c in cases if isinstance(c, dict)] != expected_ids:
        raise ValueError("Case IDs or sequence changed")
    groups = Counter()
    for item in cases:
        if not isinstance(item, dict) or set(item) != CASE_KEYS:
            raise ValueError("Unexpected case data")
        if item["category"] not in CATEGORIES:
            raise ValueError("Unexpected category")
        question = item["question"]
        if (not isinstance(question, str) or not 5 <= len(question) <= 600
                or not question.endswith((".", "?")) or
                any(prefix.lower() in question.lower() for prefix in NOTE_PREFIX)):
            raise ValueError("Invalid frozen question")
        groups[item["category"]] += 1
    if any(groups[g] != 4 for g in CATEGORIES):
        raise ValueError("Expected four cases per group")


def conservative_decision(question: str, *, budget: int = 2) -> Decision:
    """Conservative routing; no API, auto escalation or semantic guarantees."""
    if not isinstance(question, str) or not 1 <= len(question) <= 6000:
        raise ValueError("Invalid question")
    if type(budget) is not int or budget not in (0, 1, 2):
        raise ValueError("Invalid role-call budget")
    parts = NOTE_SPLIT.split(question.strip())
    body = parts[0].strip()
    annotations = parts[1:]
    if (len(annotations) > 2 or
            any(len(a) > 300 or not a.startswith(NOTE_PREFIX) for a in annotations)):
        # Unsupported annotations must not be silently ignored.
        return Decision("uncertain", 0, "noncanonical_math", 0)
    # Do not treat arbitrary extra text as an annotation.
    matched = GRAMMAR.fullmatch(body)
    if matched:
        status = "needs_review" if matched.group(3) is not None else "single"
        required = 2 if status == "needs_review" else 1
        if budget < required:
            return Decision("blocked_by_budget", 0, "budget_insufficient", len(annotations))
        return Decision(status, required,
                        "exact_two_step" if required == 2 else "exact_one_step",
                        len(annotations))
    # Number words are recognized only as bounded tokens, not as free-form arithmetic.
    maybe_math = bool(MATH_CUE.search(body) or NUMBER.findall(body) or WORD_TOKEN.search(body))
    return Decision("uncertain" if maybe_math else "unsupported", 0,
                    "noncanonical_math" if maybe_math else "no_arithmetic_intent",
                    len(annotations))


def variants(question: str, manifest: dict) -> dict:
    return {
        "base": question,
        "tagged_neutral": question + " " + manifest["tagged_neutral"],
        "tagged_format": question + " " + manifest["tagged_format"],
    }


def decision_for(question: str, identity: str, policy: str, budget: int = 2) -> Decision:
    if policy == "candidate_conservative":
        return conservative_decision(question, budget=budget)
    if policy == "baseline_length":
        route = choose(replace(task_profile(question, identity), budget=budget), "adaptive")
    elif policy == "candidate_content":
        try:
            route = candidate_route(question, identity, budget=budget)
        except ValueError as err:
            if "numeric literal" in str(err) and not NUMBER.findall(question):
                return Decision("invalid_input", 0, "missing_numeric_literal", 0)
            raise
    else:
        raise ValueError("Unknown routing policy")
    return Decision(route, planned_calls(route), "legacy_route", 0)


def _counts(counter: Counter) -> dict:
    return {s: counter[s] for s in STATES if counter[s]}


def audit(manifest: dict) -> dict:
    validate_manifest(manifest)
    route_counts = {p: {v: Counter() for v in VARIANTS} for p in POLICIES}
    group_base_routes = {p: {g: Counter() for g in CATEGORIES} for p in POLICIES}
    pair_counts = {p: {v: Counter() for v in VARIANTS[1:]} for p in POLICIES}
    planned = {p: Counter() for p in POLICIES}
    budgets = {p: {str(b): Counter() for b in (0, 1, 2)} for p in POLICIES}
    rows = []
    for item in manifest["cases"]:
        base = item["question"]
        generated = variants(base, manifest)
        by_policy = {p: {} for p in POLICIES}
        trials = []
        for variant, question in generated.items():
            entry = {"variant": variant, "question": question,
                     "word_count": len(question.split()),
                     "question_sha256": hashlib.sha256(question.encode()).hexdigest()}
            for policy in POLICIES:
                decision = decision_for(question, item["id"] + "-" + variant, policy)
                by_policy[policy][variant] = decision
                route_counts[policy][variant][decision.status] += 1
                planned[policy][variant] += decision.calls_planned
                entry[policy] = {
                    "status": decision.status, "calls_planned": decision.calls_planned,
                    "reason": decision.reason,
                    "annotations_ignored": decision.annotation_count,
                }
                if variant == "base":
                    group_base_routes[policy][item["category"]][decision.status] += 1
            trials.append(entry)
        for policy in POLICIES:
            initial = by_policy[policy]["base"].status
            for variant in VARIANTS[1:]:
                changed = by_policy[policy][variant].status
                counts = pair_counts[policy][variant]
                counts["total"] += 1
                if initial == "invalid_input":
                    counts["invalid_base"] += 1
                elif changed == "invalid_input":
                    counts["invalid_variant"] += 1
                elif initial == changed:
                    counts["unchanged"] += 1
                else:
                    counts["changed"] += 1
            for b in (0, 1, 2):
                d = decision_for(base, item["id"] + "-budget-" + str(b), policy, b)
                budgets[policy][str(b)][d.status] += 1
        rows.append({"id": item["id"], "author_category_not_oracle": item["category"],
                     "variants": trials})

    # EXP-016 is a disclosed development regression, not an independent holdout.
    regression = Counter()
    for item in load_exp016()["cases"]:
        outcome = conservative_decision(item["question"])
        regression[outcome.status] += 1
    paired = {p: {v: {x: pair_counts[p][v][x] for x in
                   ("total", "unchanged", "changed", "invalid_base", "invalid_variant")}
                  for v in VARIANTS[1:]} for p in POLICIES}
    if any(paired[p][v]["total"] != 16 for p in POLICIES for v in VARIANTS[1:]):
        raise AssertionError("Lost preregistered trials")
    return {
        "experiment": "EXP-017",
        "phase": "model_free_narrow_grammar_abstention_audit",
        "input_manifest_git_blob": FROZEN_BLOB,
        "case_count": len(rows), "entries_per_policy": len(rows) * len(VARIANTS),
        "policies": list(POLICIES),
        "pair_counts": paired,
        "route_counts": {p: {v: _counts(route_counts[p][v]) for v in VARIANTS}
                         for p in POLICIES},
        "base_group_routes": {p: {g: _counts(group_base_routes[p][g]) for g in CATEGORIES}
                              for p in POLICIES},
        "planned_role_calls_not_real_cost": {p: {v: planned[p][v] for v in VARIANTS}
                                             for p in POLICIES},
        "base_budget_route_counts": {p: {str(b): _counts(budgets[p][str(b)])
                                         for b in (0, 1, 2)} for p in POLICIES},
        "exp016_public_development_regression": _counts(regression),
        "models_called": 0, "quality_or_accuracy_measured": False,
        "independent_holdout": False, "generality_proven": False,
        "interpretation": (
            "The new candidate only commits role calls for narrow explicit arithmetic "
            "syntax, including limited English number words; all other cases abstain "
            "or are unsupported. The author designed tasks knowing the rules. "
            "Stable tags and budget accounting do not establish LLM superiority."
        ),
        "cases": rows,
    }


def summary(report: dict) -> dict:
    return {k: report[k] for k in (
        "experiment", "phase", "input_manifest_git_blob", "case_count",
        "entries_per_policy", "policies", "pair_counts", "route_counts",
        "base_group_routes", "planned_role_calls_not_real_cost",
        "base_budget_route_counts", "exp016_public_development_regression",
        "models_called", "quality_or_accuracy_measured", "independent_holdout",
        "generality_proven",
    )}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="results/exp017-conservative-audit.json")
    args = parser.parse_args(argv)
    report = audit(load_manifest())
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                    encoding="utf-8")
    print("EXP017_SUMMARY=" + json.dumps(summary(report), sort_keys=True))


if __name__ == "__main__":
    main()
