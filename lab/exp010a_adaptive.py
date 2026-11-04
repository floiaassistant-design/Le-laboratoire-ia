"""EXP-010A: model-agnostic adaptive agent orchestration.

No model API or real agents are bundled. The invoke callback supplies all
outputs. Synthetic control-flow checks are not performance results.
"""
from __future__ import annotations
import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Callable, Tuple

POLICIES = ("adaptive", "always_single", "always_parallel", "always_review")
ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}\Z")


@dataclass(frozen=True)
class Task:
    id: str
    uncertainty: int
    parallelizable: bool
    mandatory_review: bool
    budget: int

    def __post_init__(self):
        if type(self.id) is not str or not ID.fullmatch(self.id):
            raise ValueError("Invalid task ID")
        if type(self.uncertainty) is not int or self.uncertainty not in range(4):
            raise ValueError("Invalid uncertainty")
        if type(self.parallelizable) is not bool or type(self.mandatory_review) is not bool:
            raise ValueError("Invalid flags")
        if type(self.budget) is not int or not 0 <= self.budget <= 100:
            raise ValueError("Invalid budget")


@dataclass(frozen=True)
class Reply:
    text: str
    verdict: str = "none"


@dataclass(frozen=True)
class Outcome:
    route: str
    status: str
    spent: int
    final: str | None
    replies: Tuple[Reply, ...]


def choose(task: Task, policy: str = "adaptive") -> str:
    if policy not in POLICIES:
        raise ValueError("Unknown policy")
    if policy == "adaptive":
        desired = ("review" if task.mandatory_review or task.uncertainty >= 2
                   else "parallel" if task.parallelizable else "single")
    else:
        desired = policy.removeprefix("always_")
    if task.mandatory_review and desired != "review":
        return "blocked"
    if desired == "parallel" and not task.parallelizable:
        return "blocked"
    need = 1 if desired == "single" else 2
    if task.budget < need:
        if policy == "adaptive" and not task.mandatory_review and task.budget >= 1:
            return "single"
        return "blocked"
    return desired


def check(reply: Reply, role: str) -> None:
    if not isinstance(reply, Reply):
        raise TypeError("Expected Reply")
    if not isinstance(reply.text, str) or not 1 <= len(reply.text) <= 4000:
        raise ValueError("Invalid answer length")
    if role == "critic":
        if reply.verdict not in ("approve", "reject"):
            raise ValueError("Critic must approve or reject")
    elif reply.verdict != "none":
        raise ValueError("Only critic can issue a verdict")


def run(task: Task, invoke: Callable[[Task, str, Tuple[Reply, ...]], Reply],
        policy: str = "adaptive") -> Outcome:
    route = choose(task, policy)
    if route == "blocked":
        return Outcome(route, "blocked", 0, None, ())

    def call(role: str, prior: Tuple[Reply, ...]) -> Reply:
        reply = invoke(task, role, prior)
        check(reply, role)
        return reply

    first = call("solver", ())
    if route == "single":
        return Outcome(route, "complete", 1, first.text, (first,))
    if route == "parallel":
        # Independent solve never receives the other agent's answer.
        other = call("independent", ())
        equal = first.text == other.text
        return Outcome(route, "complete" if equal else "unresolved_disagreement",
                       2, first.text if equal else None, (first, other))
    critic = call("critic", (first,))
    approved = critic.verdict == "approve"
    return Outcome(route, "complete" if approved else "rejected_by_critic",
                   2, first.text if approved else None, (first, critic))


def smoke() -> dict:
    """Control-flow examples only; synthetic agents have no world knowledge."""
    samples = (
        Task("simple", 0, False, False, 1),
        Task("parallel", 0, True, False, 2),
        Task("uncertain", 3, False, False, 2),
        Task("underbudget", 0, False, True, 1),
        Task("disagreement", 0, True, False, 2),
        Task("rejection", 3, False, False, 2),
    )

    def stub(task, role, prior):
        if role == "critic":
            return Reply("synthetic review", "reject" if task.id == "rejection" else "approve")
        if role == "independent" and task.id == "disagreement":
            return Reply("different synthetic answer")
        return Reply("synthetic answer")

    results = [run(sample, stub) for sample in samples]
    return {
        "experiment": "EXP-010A",
        "phase": "synthetic_offline_smoke_only",
        "synthetic_cases": len(samples),
        "real_models_called": 0,
        "real_task_accuracy_measured": False,
        "new_scientific_discoveries": 0,
        "outcomes": [
            {"id": t.id, "route": r.route, "status": r.status, "spent": r.spent}
            for t, r in zip(samples, results)
        ],
    }


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--output", default="results/exp010a-smoke.json")
    args = p.parse_args(argv)
    record = smoke()
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("EXP010A_OFFLINE_SMOKE=" + json.dumps({"cases": record["synthetic_cases"], "models": 0}))


if __name__ == "__main__":
    main()
