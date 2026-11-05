"""EXP-014: deterministic, model-free routing sensitivity to neutral padding.

This is a design audit, not an experiment measuring actual LLM accuracy.
The arithmetic facts remain the same by construction; this does not prove
that a real model would respond equivalently after receiving extra text.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

from .exp010a_adaptive import choose
from .exp011_manual import task_profile

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "experiments" / "exp014-neutral-padding-cases.json"
PADDING = "No additional quantities or conditions are supplied here."
EXPECTED_IDS = ("add-01", "subtract-01", "multiply-01",
                "mixed-01", "mixed-02", "mixed-03")
VARIANTS = ("short", "medium", "long")
EXPECTED_ROUTE = {"short": "single", "medium": "parallel", "long": "review"}
NUMBER = re.compile(r"\d+(?:\.\d+)?")
EXACT_FIELDS = {"id", "declared_steps", "question"}


def validate_manifest(manifest: dict) -> None:
    if (not isinstance(manifest, dict)
            or manifest.get("experiment") != "EXP-014"
            or manifest.get("phase") !=
               "preregistered_model_free_length_sensitivity_audit"
            or manifest.get("status") !=
               "input_only_deterministic_preflight_no_llm"
            or manifest.get("rule_reference") !=
               "EXP-011 question_word_count_only 40/50 words, budget 2"
            or manifest.get("padding") != PADDING
            or manifest.get("categories_are_author_declared_not_measured") is not True
            or manifest.get("model_calls") != 0
            or manifest.get("answer_key_included") is not False):
        raise ValueError("Unexpected EXP-014 preregistration")
    cases = manifest.get("cases")
    if not isinstance(cases, list) or len(cases) != len(EXPECTED_IDS):
        raise ValueError("Exactly six base questions required")
    if [c.get("id") for c in cases if isinstance(c, dict)] != list(EXPECTED_IDS):
        raise ValueError("Base question IDs were changed")
    for i, item in enumerate(cases):
        if not isinstance(item, dict) or set(item) != EXACT_FIELDS:
            raise ValueError("Unexpected base question structure")
        if (type(item["declared_steps"]) is not int
                or item["declared_steps"] != (1 if i < 3 else
                                               2 if i < 5 else 3)):
            raise ValueError("Unexpected author-declared arithmetic steps")
        question = item["question"]
        if (not isinstance(question, str)
                or len(question) > 2000
                or not 4 <= len(question.split()) < 40
                or not question.endswith("?")
                or PADDING in question
                or not NUMBER.findall(question)):
            raise ValueError("Base question is invalid or already padded")
    if NUMBER.findall(PADDING):
        raise AssertionError("Neutral padding must not add digits")


def _pad(question: str, minimum: int) -> str:
    result = question
    while len(result.split()) < minimum:
        result += " " + PADDING
    return result


def variants(question: str) -> dict[str, str]:
    if not isinstance(question, str) or not 1 <= len(question.split()) < 40:
        raise ValueError("Not a short seed question")
    short = question
    medium = _pad(short, 40)
    long = _pad(medium, 50)
    words = [len(s.split()) for s in (short, medium, long)]
    if not (words[0] < 40 <= words[1] < 50 <= words[2]):
        raise AssertionError("Unexpected word-count boundaries")
    facts = NUMBER.findall(short)
    if any(NUMBER.findall(s) != facts for s in (medium, long)):
        raise AssertionError("Added numeric information")
    if any(not s.startswith(short) for s in (medium, long)):
        raise AssertionError("Base question mutated")
    if not all((s[len(short):].strip().replace(PADDING, "").strip() == "")
               for s in (medium, long)):
        raise AssertionError("Only registered padding allowed")
    return dict(zip(VARIANTS, (short, medium, long)))


def planned_calls(route: str) -> int:
    if route == "blocked":
        return 0
    if route == "single":
        return 1
    if route in ("parallel", "review"):
        return 2
    raise ValueError("Invalid route")


def audit(manifest: dict) -> dict:
    validate_manifest(manifest)
    families = []
    route_counter = {v: Counter() for v in VARIANTS}
    calls_counter = Counter()
    adjacent_changes = Counter()
    category_count = Counter()
    for case in manifest["cases"]:
        created = variants(case["question"])
        category = "one_declared_step" if case["declared_steps"] == 1 \
                   else "multiple_declared_steps"
        category_count[category] += 1
        routes = {}
        rows = []
        for kind, question in created.items():
            profile = task_profile(question, case["id"] + "-" + kind)
            route = choose(profile, "adaptive")
            if route != EXPECTED_ROUTE[kind]:
                raise AssertionError("Observed router no longer follows frozen thresholds")
            routes[kind] = route
            route_counter[kind][route] += 1
            calls = planned_calls(route)
            calls_counter[kind] += calls
            rows.append({
                "variant": kind,
                "question": question,
                "word_count": len(question.split()),
                "question_sha256": hashlib.sha256(question.encode("utf-8")).hexdigest(),
                "route": route,
                "planned_role_calls": calls,
            })
        if routes["short"] != routes["medium"]:
            adjacent_changes["short_to_medium"] += 1
        if routes["medium"] != routes["long"]:
            adjacent_changes["medium_to_long"] += 1
        if routes["short"] != routes["long"]:
            adjacent_changes["short_to_long"] += 1
        families.append({
            "id": case["id"],
            "declared_steps_not_measured_difficulty": case["declared_steps"],
            "author_category": category,
            "question_facts_preserved_as_numeric_tokens": True,
            "only_registered_padding_appended": True,
            "variants": rows,
        })
    n = len(families)
    return {
        "experiment": "EXP-014",
        "phase": "deterministic_adversarial_input_audit_no_model",
        "source_manifest_sha256": hashlib.sha256(
            json.dumps(manifest, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest(),
        "base_families": n,
        "variants_per_family": len(VARIANTS),
        "total_input_variants": n * len(VARIANTS),
        "categories_author_declared_not_measured": dict(category_count),
        "route_counts": {v: dict(route_counter[v]) for v in VARIANTS},
        "route_changes_by_pair": {k: adjacent_changes[k] for k in
                                  ("short_to_medium", "medium_to_long", "short_to_long")},
        "planned_role_calls_by_variant": {k: calls_counter[k] for k in VARIANTS},
        "short_to_long_role_call_ratio": (
            calls_counter["long"] / calls_counter["short"]),
        "model_calls_executed": 0,
        "model_accuracy_or_latency_measured": False,
        "cognitive_semantic_equivalence_proven": False,
        "future_model_superiority_proven": False,
        "results_mechanical_not_statistical": True,
        "interpretation": (
            "The same declared arithmetic facts, with only repeated neutral "
            "sentences, cross the word-count thresholds and change planned "
            "routes. This exposes a deterministic sensitivity by construction, "
            "not an observed LLM error, routing benefit, or causal finding. "
            "Semantic invariance for an LLM has not been demonstrated."
        ),
        "families": families,
    }


def main(argv=None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="results/exp014-neutral-padding-audit.json")
    args = parser.parse_args(argv)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    report = audit(manifest)
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, ensure_ascii=False,
                                      sort_keys=True) + "\n", encoding="utf-8")
    print("EXP014_OFFLINE_ONLY=" + json.dumps({
        "families": report["base_families"],
        "route_flips_short_to_long": report["route_changes_by_pair"]["short_to_long"],
        "models_called": report["model_calls_executed"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
