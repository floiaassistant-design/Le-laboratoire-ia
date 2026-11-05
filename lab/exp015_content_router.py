"""EXP-015: candidate content-feature routing, model-free design audit.

This candidate is deliberately simple and post-hoc relative to EXP-014.
It MUST NOT replace the frozen EXP-011 length router or be advertised as
empirically more accurate. No network, model, answer oracle or API is used.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

from .exp010a_adaptive import Task, choose
from .exp011_manual import task_profile
from .exp014_neutral_padding import (
    MANIFEST, NUMBER, VARIANTS, planned_calls, validate_manifest, variants,
)

STAGE = re.compile(r"\b(?:then|later)\b", re.IGNORECASE)
NEGATIVE_CONTROL = "Then answer with the result."
ROUTES = ("single", "parallel", "review", "blocked")


def content_profile(question: str, identity: str, *, budget: int = 2) -> Task:
    """Input-only unvalidated heuristic; insensitive to word count."""
    if not isinstance(question, str) or not 1 <= len(question) <= 6000:
        raise ValueError("Invalid question")
    literals = NUMBER.findall(question)
    if not literals:
        raise ValueError("At least one written numeric literal is required")
    stages = bool(STAGE.search(question))
    return Task(
        id=identity,
        uncertainty=2 if stages else 0,
        parallelizable=len(literals) >= 3,
        mandatory_review=False,
        budget=budget,
    )


def candidate_route(question: str, identity: str, *, budget: int = 2) -> str:
    return choose(content_profile(question, identity, budget=budget), "adaptive")


def _route_count(counter: Counter) -> dict:
    return {route: counter[route] for route in ROUTES if counter[route]}


def audit(manifest: dict) -> dict:
    validate_manifest(manifest)
    baseline_counts = {variant: Counter() for variant in VARIANTS}
    candidate_counts = {variant: Counter() for variant in VARIANTS}
    baseline_calls = Counter()
    candidate_calls = Counter()
    baseline_flips = 0
    candidate_flips = 0
    negative_flips = 0
    families = []

    for case in manifest["cases"]:
        family_id = case["id"]
        questions = variants(case["question"])
        rows = []
        base_routes = {}
        test_routes = {}

        for variant, question in questions.items():
            old = choose(task_profile(question, family_id + "-" + variant), "adaptive")
            new = candidate_route(question, family_id + "-" + variant)
            base_routes[variant] = old
            test_routes[variant] = new
            baseline_counts[variant][old] += 1
            candidate_counts[variant][new] += 1
            baseline_calls[variant] += planned_calls(old)
            candidate_calls[variant] += planned_calls(new)
            rows.append({
                "variant": variant,
                "word_count": len(question.split()),
                "question_sha256": hashlib.sha256(question.encode("utf-8")).hexdigest(),
                "numeric_literal_count": len(NUMBER.findall(question)),
                "stage_marker_present": bool(STAGE.search(question)),
                "baseline_route": old,
                "candidate_route": new,
                "baseline_planned_calls": planned_calls(old),
                "candidate_planned_calls": planned_calls(new),
            })

        negative_question = case["question"] + " " + NEGATIVE_CONTROL
        if NUMBER.findall(negative_question) != NUMBER.findall(case["question"]):
            raise AssertionError("Negative control changed numeric literal tokens")
        negative_route = candidate_route(negative_question, family_id + "-negative")
        if negative_route != test_routes["short"]:
            negative_flips += 1
        if base_routes["short"] != base_routes["long"]:
            baseline_flips += 1
        if test_routes["short"] != test_routes["long"]:
            candidate_flips += 1
        families.append({
            "id": family_id,
            "declared_steps_not_measured_difficulty": case["declared_steps"],
            "variants": rows,
            "negative_control_suffix": NEGATIVE_CONTROL,
            "negative_control_route": negative_route,
            "negative_control_route_changed": negative_route != test_routes["short"],
        })

    return {
        "experiment": "EXP-015",
        "phase": "retrospective_design_audit_no_model",
        "source_manifest_sha256": hashlib.sha256(
            json.dumps(manifest, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest(),
        "base_families": len(families),
        "total_input_variants": len(families) * len(VARIANTS),
        "baseline_route_counts": {v: _route_count(baseline_counts[v]) for v in VARIANTS},
        "candidate_route_counts": {v: _route_count(candidate_counts[v]) for v in VARIANTS},
        "baseline_planned_calls": {v: baseline_calls[v] for v in VARIANTS},
        "candidate_planned_calls": {v: candidate_calls[v] for v in VARIANTS},
        "baseline_short_to_long_flips": baseline_flips,
        "candidate_short_to_long_flips": candidate_flips,
        "candidate_negative_control_flips": negative_flips,
        "models_called": 0,
        "real_model_accuracy_or_cost_measured": False,
        "independent_out_of_sample_evaluation": False,
        "general_paraphrase_robustness_proven": False,
        "content_features_selected_after_seeing_cases": True,
        "interpretation": (
            "The candidate is stable for the registered neutral EXP-014 padding, "
            "but fails on some innocuous stage-word additions. Its rules were "
            "selected with knowledge of these six cases; no independent "
            "validation, model quality, financial saving or superiority follows."
        ),
        "families": families,
    }


def summary(report: dict) -> dict:
    """Permanent allowlisted deterministic summary, never real performance."""
    fields = (
        "experiment", "phase", "source_manifest_sha256", "base_families",
        "total_input_variants", "baseline_route_counts", "candidate_route_counts",
        "baseline_planned_calls", "candidate_planned_calls",
        "baseline_short_to_long_flips", "candidate_short_to_long_flips",
        "candidate_negative_control_flips", "models_called",
        "real_model_accuracy_or_cost_measured",
        "independent_out_of_sample_evaluation",
        "general_paraphrase_robustness_proven",
        "content_features_selected_after_seeing_cases",
    )
    return {key: report[key] for key in fields}


def main(argv=None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="results/exp015-content-router-audit.json")
    args = parser.parse_args(argv)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    report = audit(manifest)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                   encoding="utf-8")
    print("EXP015_MODEL_FREE=" + json.dumps({
        "families": report["base_families"],
        "baseline_flips": report["baseline_short_to_long_flips"],
        "candidate_flips": report["candidate_short_to_long_flips"],
        "negative_control_flips": report["candidate_negative_control_flips"],
        "models_called": report["models_called"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
