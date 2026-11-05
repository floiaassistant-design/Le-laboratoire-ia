"""EXP-016 — frozen-input routing stress test; NO LLM calls or measured accuracy."""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import re

from .exp010a_adaptive import Task, choose
from .exp011_manual import task_profile
from .exp014_neutral_padding import NUMBER, planned_calls
from .exp015_content_router import STAGE, candidate_route

ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = ROOT / "experiments" / "exp016-cases.json"
FROZEN_MANIFEST_BLOB = "71fc6eb6ca88f3a412faf9a019e824caacc4f9cd"
GROUPS = (
    "simple_two_literals", "simple_three_literals",
    "multistep_marked", "multistep_unmarked",
)
VARIANTS = ("base", "neutral_padding", "number_words", "misleading_stage", "stage_removed")
TRANSFORMS = VARIANTS[1:]
ROUTES = ("single", "parallel", "review", "blocked", "invalid_input")
EXACT_MANIFEST_KEYS = {
    "experiment", "phase", "status", "model_calls", "answer_key_included",
    "semantic_equivalence_human_asserted_not_model_verified",
    "neutral_padding", "misleading_stage_suffix", "stage_replacement",
    "padding_min_words", "cases",
}
EXACT_CASE_KEYS = {"id", "category", "author_declared_steps", "question", "number_words"}
NEUTRAL = "This background note adds no quantities and changes no calculation requirements."
MISLEADING = "For formatting only, write the word then after your answer."
STAGE_CONNECTOR = re.compile(r"\b(?:then|later)\b", flags=re.I)
ID = re.compile(r"(?:s2|s3|mm|mu)-0[1-4]\Z")


def git_blob(payload: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(payload)).encode("ascii") + b"\x00" + payload
    ).hexdigest()


def load_frozen_manifest(path: Path = MANIFEST_PATH) -> dict:
    raw = path.read_bytes()
    if git_blob(raw) != FROZEN_MANIFEST_BLOB:
        raise ValueError("EXP-016 frozen input manifest has been altered")
    data = json.loads(raw.decode("utf-8"))
    validate_manifest(data)
    return data


def validate_manifest(data: dict) -> None:
    if not isinstance(data, dict) or set(data) != EXACT_MANIFEST_KEYS:
        raise ValueError("Invalid manifest keys")
    if (
        data["experiment"] != "EXP-016"
        or data["phase"] != "preregistered_new_author_constructed_inputs_before_candidate_routes"
        or data["status"] != "frozen_inputs_no_observed_routes"
        or data["model_calls"] != 0
        or data["answer_key_included"] is not False
        or data["semantic_equivalence_human_asserted_not_model_verified"] is not True
        or data["neutral_padding"] != NEUTRAL
        or data["misleading_stage_suffix"] != MISLEADING
        or data["stage_replacement"] != "afterward"
        or type(data["padding_min_words"]) is not int
        or data["padding_min_words"] != 60
    ):
        raise ValueError("EXP-016 parameters do not match preregistration")
    if NUMBER.findall(NEUTRAL) or STAGE.search(NEUTRAL):
        raise AssertionError("Unexpected numbers or stage words in neutral padding")
    if NUMBER.findall(MISLEADING) or not STAGE.search(MISLEADING):
        raise AssertionError("Misleading control must add a stage word but no digits")
    cases = data.get("cases")
    if not isinstance(cases, list) or len(cases) != 16:
        raise ValueError("All 16 frozen cases required")
    expected_ids = [prefix + "-" + str(i).zfill(2)
                    for prefix in ("s2", "s3", "mm", "mu")
                    for i in range(1, 5)]
    if [x.get("id") for x in cases if isinstance(x, dict)] != expected_ids:
        raise ValueError("Case identity/order changed")
    counts = Counter()
    for case in cases:
        if not isinstance(case, dict) or set(case) != EXACT_CASE_KEYS:
            raise ValueError("Unexpected case schema")
        group, question = case["category"], case["question"]
        if group not in GROUPS or not isinstance(question, str):
            raise ValueError("Invalid group/question")
        counts[group] += 1
        if not 10 <= len(question.split()) < 60:
            raise ValueError("Unexpected base question length")
        marked = bool(STAGE.search(question))
        if marked != (group == "multistep_marked"):
            raise ValueError("Transition word grouping changed")
        steps = 1 if group.startswith("simple") else 2
        if type(case["author_declared_steps"]) is not int or case["author_declared_steps"] != steps:
            raise ValueError("Author annotations changed")
        literals = NUMBER.findall(question)
        if len(literals) != (2 if group == "simple_two_literals" else
                             3 if group in ("simple_three_literals", "multistep_unmarked")
                             else len(literals)):
            raise ValueError("Unexpected number of literals in frozen group")
        if not 2 <= len(literals) <= 3:
            raise ValueError("Unexpected literal count")
        replacements = case["number_words"]
        if not isinstance(replacements, dict) or set(replacements) != set(literals):
            raise ValueError("Word spelling map incomplete")
        for digit, word in replacements.items():
            if not isinstance(word, str) or not re.fullmatch(r"[a-z]+(?:-[a-z]+)?", word):
                raise ValueError("Invalid number-word encoding")
            if NUMBER.findall(word):
                raise ValueError("Number word includes digits")
    if any(counts[group] != 4 for group in GROUPS):
        raise ValueError("Expected four examples in each category")


def make_variants(case: dict, manifest: dict) -> dict[str, str]:
    q = case["question"]
    words = q
    while len(words.split()) < manifest["padding_min_words"]:
        words += " " + manifest["neutral_padding"]
    if NUMBER.findall(words) != NUMBER.findall(q):
        raise AssertionError("Neutral padding changed arithmetic number literals")
    word_replaced = NUMBER.sub(lambda m: case["number_words"][m.group()], q)
    if NUMBER.findall(word_replaced):
        raise AssertionError("Words variant still contains numeric literal")
    misleading = q + " " + manifest["misleading_stage_suffix"]
    if NUMBER.findall(misleading) != NUMBER.findall(q):
        raise AssertionError("Misleading control added arithmetic number")
    variants = {
        "base": q,
        "neutral_padding": words,
        "number_words": word_replaced,
        "misleading_stage": misleading,
    }
    if case["category"] == "multistep_marked":
        removed, n = STAGE_CONNECTOR.subn(manifest["stage_replacement"], q)
        if n != 1 or STAGE.search(removed) or NUMBER.findall(removed) != NUMBER.findall(q):
            raise AssertionError("Exactly one stage connector must be swapped")
        variants["stage_removed"] = removed
    return variants


def _route(question: str, identifier: str, policy: str, budget: int = 2) -> str:
    if policy == "baseline_length":
        profile = replace(task_profile(question, identifier), budget=budget)
        return choose(profile, "adaptive")
    if policy == "candidate_content":
        try:
            return candidate_route(question, identifier, budget=budget)
        except ValueError as exc:
            # Missing digits is known rejection, not a zero-cost execution or
            # a routing decision. Unexpected invalid IDs are never swallowed.
            if not NUMBER.findall(question) and "numeric literal" in str(exc):
                return "invalid_input"
            raise
    raise ValueError("Unknown policy")


def _ordered_counts(counts: Counter) -> dict:
    return {x: counts[x] for x in ROUTES if counts[x]}


def audit(manifest: dict) -> dict:
    validate_manifest(manifest)
    policies = ("baseline_length", "candidate_content")
    pair_totals = {p: {name: Counter() for name in TRANSFORMS} for p in policies}
    route_counts = {p: {v: Counter() for v in VARIANTS} for p in policies}
    role_calls = {p: Counter() for p in policies}
    category_base_routes = {p: {g: Counter() for g in GROUPS} for p in policies}
    unreviewed_multistep = Counter()
    budget_counts = {p: {str(n): Counter() for n in (0, 1, 2)} for p in policies}
    families = []

    for case in manifest["cases"]:
        kind = case["category"]
        generated = make_variants(case, manifest)
        route_for = {p: {} for p in policies}
        rows = []
        for variant, question in generated.items():
            entry = {
                "variant": variant, "question": question,
                "question_sha256": hashlib.sha256(question.encode("utf-8")).hexdigest(),
                "word_count": len(question.split()),
                "numeric_literal_count": len(NUMBER.findall(question)),
                "stage_marker_present": bool(STAGE.search(question)),
            }
            for policy in policies:
                route = _route(question, case["id"] + "-" + variant, policy)
                route_for[policy][variant] = route
                entry[policy + "_route"] = route
                entry[policy + "_planned_calls"] = (
                    None if route == "invalid_input" else planned_calls(route)
                )
                route_counts[policy][variant][route] += 1
                if route != "invalid_input":
                    role_calls[policy][variant] += planned_calls(route)
                if variant == "base":
                    category_base_routes[policy][kind][route] += 1
                    if case["author_declared_steps"] > 1 and route != "review":
                        unreviewed_multistep[policy] += 1
            rows.append(entry)

        for policy in policies:
            initial = route_for[policy]["base"]
            for variant in generated:
                if variant == "base":
                    continue
                row = pair_totals[policy][variant]
                row["total"] += 1
                route = route_for[policy][variant]
                if initial == "invalid_input":
                    row["invalid_base"] += 1
                elif route == "invalid_input":
                    row["invalid_variant"] += 1
                elif initial == route:
                    row["unchanged"] += 1
                else:
                    row["changed"] += 1
            for budget in (0, 1, 2):
                route = _route(case["question"], case["id"] + "-b" + str(budget),
                               policy, budget)
                budget_counts[policy][str(budget)][route] += 1
        families.append({
            "id": case["id"], "author_category_not_validated_difficulty": kind,
            "author_declared_steps_not_oracle": case["author_declared_steps"],
            "variants": rows,
        })

    pair_reports = {
        policy: {
            t: {key: pair_totals[policy][t][key]
                for key in ("total", "unchanged", "changed", "invalid_base", "invalid_variant")}
            for t in TRANSFORMS
        } for policy in policies
    }
    if any(pair_reports[p][t]["total"] != (4 if t == "stage_removed" else 16)
           for p in policies for t in TRANSFORMS):
        raise AssertionError("Experiment denominator changed")
    return {
        "experiment": "EXP-016",
        "phase": "author_constructed_input_only_routing_stress_not_blind",
        "source_manifest_git_blob_sha": FROZEN_MANIFEST_BLOB,
        "base_families": len(families),
        "total_variants_per_policy": sum(len(f["variants"]) for f in families),
        "categories_author_declared_not_validation": True,
        "policies": list(policies),
        "pair_counts": pair_reports,
        "route_counts": {
            p: {v: _ordered_counts(route_counts[p][v]) for v in VARIANTS}
            for p in policies
        },
        "planned_calls_for_valid_routes_only": {
            p: {v: role_calls[p][v] for v in VARIANTS} for p in policies
        },
        "base_category_routes": {
            p: {g: _ordered_counts(category_base_routes[p][g]) for g in GROUPS}
            for p in policies
        },
        "author_multistep_not_review": dict(unreviewed_multistep),
        "budget_base_routes": {
            p: {budget: _ordered_counts(budget_counts[p][budget])
                for budget in ("0", "1", "2")} for p in policies
        },
        "models_called": 0,
        "answer_correctness_or_cost_measured": False,
        "blind_or_representative_sample": False,
        "semantic_equivalence_independently_verified": False,
        "interpretation": (
            "These are input-only route choices on newly authored examples with "
            "known heuristic rules, not blind validation or model performance. "
            "Invalid input is distinct from blocked, route changes and zero calls."
        ),
        "families": families,
    }


def summary(report: dict) -> dict:
    """Allowlisted output for durable revalidation; no raw model answers."""
    fields = (
        "experiment", "phase", "source_manifest_git_blob_sha", "base_families",
        "total_variants_per_policy", "categories_author_declared_not_validation",
        "policies", "pair_counts", "route_counts", "planned_calls_for_valid_routes_only",
        "base_category_routes", "author_multistep_not_review", "budget_base_routes",
        "models_called", "answer_correctness_or_cost_measured",
        "blind_or_representative_sample", "semantic_equivalence_independently_verified",
    )
    return {key: report[key] for key in fields}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="results/exp016-routing-stress-audit.json")
    args = parser.parse_args(argv)
    report = audit(load_frozen_manifest())
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                    encoding="utf-8")
    print("EXP016_SUMMARY=" + json.dumps(summary(report), sort_keys=True))


if __name__ == "__main__":
    main()
