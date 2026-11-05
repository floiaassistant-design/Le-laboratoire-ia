"""EXP-018: natural-language routing coverage audit, with no model calls.

Author-constructed, non-blind examples. This audits decisions and abstentions,
NOT LLM problem solving, accuracy, quality, or monetary costs.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

from .exp014_neutral_padding import NUMBER
from .exp017_conservative import (
    POLICIES, STATES, decision_for, git_blob,
)

ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = ROOT / "experiments" / "exp018-cases.json"
FROZEN_MANIFEST_BLOB = "5b82e3850d7888c8174e7b1e50979a9dd2a011d4"
CATEGORIES = (
    "natural_single_digits", "natural_multistep_digits",
    "number_words_only", "implicit_operations_digits",
    "non_arithmetic", "math_with_format_digits",
)
ID_PREFIX = ("s", "m", "w", "i", "n", "f")
WORD_VARIANT_GROUPS = (
    "natural_single_digits", "natural_multistep_digits",
    "implicit_operations_digits", "math_with_format_digits",
)
VARIANTS = ("base", "paraphrase", "polite", "background",
            "embedded_format", "number_words")
TRANSFORMS = VARIANTS[1:]
ROLE_STATES = frozenset(("single", "parallel", "review", "needs_review"))
ABSTAIN_STATES = frozenset(("uncertain", "unsupported"))
BLOCKED_STATES = frozenset(("blocked", "blocked_by_budget"))
POLITE = "Please keep your reply short."
BACKGROUND = "This question comes from an everyday conversation."
FORMAT = "Put your final response in bold text."
TOP_FIELDS = {
    "experiment", "phase", "status", "language", "provenance",
    "model_calls", "answer_key_included", "polite_suffix",
    "background_suffix", "embedded_format_suffix", "cases",
}
CASE_FIELDS = {
    "id", "category", "author_math_intent",
    "question", "paraphrase", "digit_spellings",
}


def load_manifest(path: Path = MANIFEST_PATH) -> dict:
    raw = path.read_bytes()
    if git_blob(raw) != FROZEN_MANIFEST_BLOB:
        raise ValueError("EXP-018 frozen manifest blob changed")
    data = json.loads(raw.decode("utf-8"))
    validate_manifest(data)
    return data


def validate_manifest(data: dict) -> None:
    if not isinstance(data, dict) or set(data) != TOP_FIELDS:
        raise ValueError("Unexpected EXP-018 manifest schema")
    if (data["experiment"] != "EXP-018"
            or data["phase"] != "frozen_author_constructed_new_questions_before_routing"
            or data["status"] != "inputs_only_zero_model_calls"
            or data["language"] != "en"
            or data["provenance"] != "original_author_constructed_not_random_sample"
            or type(data["model_calls"]) is not int or data["model_calls"] != 0
            or data["answer_key_included"] is not False
            or data["polite_suffix"] != POLITE
            or data["background_suffix"] != BACKGROUND
            or data["embedded_format_suffix"] != FORMAT):
        raise ValueError("EXP-018 preregistration differs from frozen parameters")
    if any(NUMBER.findall(text) for text in (POLITE, BACKGROUND, FORMAT)):
        raise AssertionError("Fixed annotation may not add digits")

    cases = data.get("cases")
    if not isinstance(cases, list) or len(cases) != 24:
        raise ValueError("Exactly 24 cases required")
    expected_ids = [prefix + "-" + str(n).zfill(2)
                    for prefix in ID_PREFIX for n in range(1, 5)]
    if [x.get("id") for x in cases if isinstance(x, dict)] != expected_ids:
        raise ValueError("Case identities/order changed")
    category_counts = Counter()
    for case in cases:
        if not isinstance(case, dict) or set(case) != CASE_FIELDS:
            raise ValueError("Malformed case")
        cat = case["category"]
        if cat not in CATEGORIES:
            raise ValueError("Unknown category")
        category_counts[cat] += 1
        if case["author_math_intent"] is not (cat != "non_arithmetic"):
            raise ValueError("Author intent flag differs from category")
        for name in ("question", "paraphrase"):
            value = case[name]
            if (not isinstance(value, str) or not 12 <= len(value) <= 500
                    or not value[-1] in ".?"
                    or "\n" in value):
                raise ValueError("Invalid question/paraphrase")
        spellings = case["digit_spellings"]
        if not isinstance(spellings, dict):
            raise ValueError("Invalid number spelling map")
        matches = NUMBER.findall(case["question"])
        must_convert = cat in WORD_VARIANT_GROUPS
        if must_convert:
            if not matches or set(spellings) != set(matches):
                raise ValueError("Number-word mapping incomplete")
            for key, value in spellings.items():
                if (not key.isdecimal() or not isinstance(value, str) or not value
                        or not all(c.isalpha() or c == "-" for c in value)
                        or NUMBER.findall(value)):
                    raise ValueError("Invalid numeric spelling")
        elif spellings:
            raise ValueError("Unregistered number-word transformation")
        if cat == "number_words_only" and matches:
            raise ValueError("Words-only case unexpectedly has digits")
    if any(category_counts[c] != 4 for c in CATEGORIES):
        raise ValueError("Missing a category member")


def make_variants(case: dict, manifest: dict) -> dict[str, str]:
    question = case["question"]
    variants = {
        "base": question,
        "paraphrase": case["paraphrase"],
        "polite": question + " " + manifest["polite_suffix"],
        "background": question + " " + manifest["background_suffix"],
        "embedded_format": question + " " + manifest["embedded_format_suffix"],
    }
    for name in ("polite", "background", "embedded_format"):
        if NUMBER.findall(variants[name]) != NUMBER.findall(question):
            raise AssertionError("Fixed suffix changed digit tokens")
    if case["category"] in WORD_VARIANT_GROUPS:
        numbered = NUMBER.sub(lambda m: case["digit_spellings"][m.group()], question)
        if NUMBER.findall(numbered):
            raise AssertionError("Number-word variant still contains digits")
        variants["number_words"] = numbered
    return variants


def _ordered_counts(counter: Counter) -> dict:
    return {s: counter[s] for s in STATES if counter[s]}


def _metric(total: int, math_n: int, role_n: int, math_without: int,
            nonmath_role: int, abstained: int, invalid: int, blocked: int,
            role_calls: int) -> dict:
    return {
        "total": total,
        "author_math_intent": math_n,
        "author_nonmath_intent": total - math_n,
        "assigned_role": role_n,
        "author_math_without_role": math_without,
        "author_nonmath_assigned_role": nonmath_role,
        "abstained_uncertain_or_unsupported": abstained,
        "invalid_input": invalid,
        "blocked": blocked,
        "role_calls_planned_on_valid_only": role_calls,
        "role_calls_are_not_actual_model_invocations": True,
    }


def audit(manifest: dict) -> dict:
    validate_manifest(manifest)
    route_counts = {p: {v: Counter() for v in VARIANTS} for p in POLICIES}
    category_base_counts = {p: {c: Counter() for c in CATEGORIES} for p in POLICIES}
    pairs = {p: {v: Counter() for v in TRANSFORMS} for p in POLICIES}
    budgets = {p: {str(b): Counter() for b in (0, 1, 2)} for p in POLICIES}
    metrics = {p: {"base": Counter(), "all": Counter()} for p in POLICIES}
    cases_out = []

    def observe_metric(policy: str, scope: str, label: bool, status: str,
                       calls_planned: int | None) -> None:
        out = metrics[policy][scope]
        out["total"] += 1
        if label:
            out["math"] += 1
        if status in ROLE_STATES:
            out["role"] += 1
            if not label:
                out["nonmath_role"] += 1
        elif label:
            out["math_without"] += 1
        if status in ABSTAIN_STATES:
            out["abstained"] += 1
        if status == "invalid_input":
            out["invalid"] += 1
        if status in BLOCKED_STATES:
            out["blocked"] += 1
        if calls_planned is not None:
            out["calls"] += calls_planned

    for case in manifest["cases"]:
        generated = make_variants(case, manifest)
        family_routes = {p: {} for p in POLICIES}
        family_rows = []
        for variant, question in generated.items():
            row = {
                "variant": variant,
                "question": question,
                "author_math_intent_not_independent_oracle": case["author_math_intent"],
                "word_count": len(question.split()),
                "digit_count": len(NUMBER.findall(question)),
                "routes": {},
            }
            for policy in POLICIES:
                dec = decision_for(question, case["id"] + "-" + variant, policy, 2)
                family_routes[policy][variant] = dec.status
                planned = None if dec.status == "invalid_input" else dec.calls_planned
                row["routes"][policy] = {
                    "status": dec.status, "planned_calls": planned,
                    "reason": dec.reason,
                }
                route_counts[policy][variant][dec.status] += 1
                observe_metric(policy, "all", case["author_math_intent"], dec.status, planned)
                if variant == "base":
                    category_base_counts[policy][case["category"]][dec.status] += 1
                    observe_metric(policy, "base", case["author_math_intent"],
                                   dec.status, planned)
            family_rows.append(row)

        for policy in POLICIES:
            base = family_routes[policy]["base"]
            for variant in generated:
                if variant == "base":
                    continue
                current = family_routes[policy][variant]
                counts = pairs[policy][variant]
                counts["total"] += 1
                if base == "invalid_input":
                    counts["invalid_base"] += 1
                elif current == "invalid_input":
                    counts["invalid_variant"] += 1
                elif current == base:
                    counts["unchanged"] += 1
                else:
                    counts["changed"] += 1
            for budget in (0, 1, 2):
                current = decision_for(case["question"], case["id"] + "-b" + str(budget),
                                       policy, budget).status
                budgets[policy][str(budget)][current] += 1
        cases_out.append({
            "id": case["id"], "author_category_not_independent_oracle": case["category"],
            "author_math_intent_not_independent_oracle": case["author_math_intent"],
            "variants": family_rows,
        })

    per_policy_metrics = {
        p: {scope: _metric(
            t["total"], t["math"], t["role"], t["math_without"],
            t["nonmath_role"], t["abstained"], t["invalid"], t["blocked"],
            t["calls"],
        ) for scope, t in metrics[p].items()} for p in POLICIES
    }
    paired = {
        p: {v: {key: pairs[p][v][key] for key in
                ("total", "unchanged", "changed", "invalid_base", "invalid_variant")}
            for v in TRANSFORMS} for p in POLICIES
    }
    for p in POLICIES:
        if per_policy_metrics[p]["all"]["total"] != 136:
            raise AssertionError("Total roster does not match preregistration")
        for v in TRANSFORMS:
            row = paired[p][v]
            if row["total"] != (16 if v == "number_words" else 24):
                raise AssertionError("Transformation denominator changed")
            if sum(row[k] for k in ("unchanged", "changed", "invalid_base",
                                   "invalid_variant")) != row["total"]:
                raise AssertionError("Misclassified routing pair")
        if any(sum(budgets[p][str(b)].values()) != 24 for b in (0, 1, 2)):
            raise AssertionError("Budget cohort not complete")

    return {
        "experiment": "EXP-018",
        "phase": "constructed_natural_language_input_only_no_model",
        "input_manifest_git_blob": FROZEN_MANIFEST_BLOB,
        "policies": list(POLICIES),
        "base_cases": len(cases_out),
        "variants_per_policy": sum(len(c["variants"]) for c in cases_out),
        "categories_author_labeled_not_intent_oracle": True,
        "route_counts_by_variant": {
            p: {v: _ordered_counts(route_counts[p][v]) for v in VARIANTS}
            for p in POLICIES
        },
        "base_category_route_counts": {
            p: {g: _ordered_counts(category_base_counts[p][g]) for g in CATEGORIES}
            for p in POLICIES
        },
        "pair_counts": paired,
        "base_and_all_metrics": per_policy_metrics,
        "budget_base_routes": {
            p: {str(b): _ordered_counts(budgets[p][str(b)]) for b in (0, 1, 2)}
            for p in POLICIES
        },
        "model_calls_executed": 0,
        "model_accuracy_latency_cost_measured": False,
        "blind_representative_or_independent": False,
        "semantic_equivalence_for_llms_proven": False,
        "interpretation": (
            "The authored intent labels and fixed natural-language requests test "
            "mechanical role assignment and abstention, not an LLM's accuracy, "
            "real-world safety or monetary savings. All no-route decisions stay "
            "in each denominator and no existing router was changed."
        ),
        "cases": cases_out,
    }


def summary(report: dict) -> dict:
    """Durable model-free aggregate; no transcript or real-model answer."""
    fields = (
        "experiment", "phase", "input_manifest_git_blob", "policies",
        "base_cases", "variants_per_policy",
        "categories_author_labeled_not_intent_oracle",
        "route_counts_by_variant", "base_category_route_counts", "pair_counts",
        "base_and_all_metrics", "budget_base_routes",
        "model_calls_executed", "model_accuracy_latency_cost_measured",
        "blind_representative_or_independent",
        "semantic_equivalence_for_llms_proven",
    )
    return {key: report[key] for key in fields}


def main(argv=None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="results/exp018-natural-coverage-audit.json")
    args = parser.parse_args(argv)
    report = audit(load_manifest())
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                    encoding="utf-8")
    print("EXP018_SUMMARY=" + json.dumps(summary(report), sort_keys=True))


if __name__ == "__main__":
    main()
