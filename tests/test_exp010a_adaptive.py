"""No-network synthetic validation of EXP-010A."""
import unittest
from lab.exp010a_adaptive import Task, Reply, choose, run, smoke


def stub(task, role, prior):
    return Reply("reviewed", "approve") if role == "critic" else Reply("answer")


class AdaptiveRoutingTests(unittest.TestCase):
    def test_simple_uses_one_call(self):
        o = run(Task("simple", 0, False, False, 3), stub)
        self.assertEqual((o.route, o.spent, o.status), ("single", 1, "complete"))

    def test_parallel_uses_two_calls(self):
        o = run(Task("parallel", 0, True, False, 2), stub)
        self.assertEqual((o.route, o.spent), ("parallel", 2))

    def test_uncertainty_selects_review(self):
        self.assertEqual(choose(Task("uncertain", 2, False, False, 2)), "review")

    def test_mandatory_review_underbudget_is_blocked(self):
        self.assertEqual(choose(Task("critical", 0, False, True, 1)), "blocked")

    def test_blocked_makes_no_calls(self):
        def forbidden(*args):
            raise AssertionError("should not invoke")
        o = run(Task("critical", 0, False, True, 1), forbidden)
        self.assertEqual((o.spent, o.final, o.status), (0, None, "blocked"))

    def test_parallel_is_truly_independent(self):
        seen = []
        def agent(task, role, prior):
            seen.append((role, prior))
            return Reply("same")
        run(Task("separate", 0, True, False, 2), agent)
        self.assertEqual(seen, [("solver", ()), ("independent", ())])

    def test_critic_sees_first_answer(self):
        seen = []
        def agent(task, role, prior):
            seen.append((role, prior))
            return stub(task, role, prior)
        run(Task("audit", 3, False, False, 2), agent)
        self.assertEqual(seen[1], ("critic", (Reply("answer"),)))

    def test_disagreement_not_silently_resolved(self):
        o = run(Task("disagree", 0, True, False, 2),
                lambda task, role, prior: Reply(role))
        self.assertEqual((o.status, o.final), ("unresolved_disagreement", None))

    def test_critic_can_accept(self):
        o = run(Task("accept", 3, False, False, 2), stub)
        self.assertEqual((o.status, o.final), ("complete", "answer"))

    def test_critic_can_reject(self):
        def agent(task, role, prior):
            return Reply("no", "reject") if role == "critic" else Reply("claim")
        o = run(Task("reject", 3, False, False, 2), agent)
        self.assertEqual((o.status, o.final), ("rejected_by_critic", None))

    def test_adaptive_can_fallback_if_no_mandatory_review(self):
        self.assertEqual(choose(Task("limited", 3, False, False, 1)), "single")

    def test_fixed_review_policy_never_silently_falls_back(self):
        self.assertEqual(choose(Task("fixed", 1, False, False, 1),
                                "always_review"), "blocked")

    def test_single_baseline_respects_mandatory_review(self):
        self.assertEqual(choose(Task("safety", 0, False, True, 3),
                                "always_single"), "blocked")

    def test_parallel_baseline_requires_parallel_task(self):
        self.assertEqual(choose(Task("seq", 0, False, False, 3),
                                "always_parallel"), "blocked")

    def test_bad_metadata_is_rejected(self):
        base = {"id": "valid", "uncertainty": 0, "parallelizable": False,
                "mandatory_review": False, "budget": 2}
        for change in ({"id": "../bad"}, {"uncertainty": True},
                       {"uncertainty": 4}, {"parallelizable": 1},
                       {"mandatory_review": 1}, {"budget": -1},
                       {"budget": True}):
            with self.subTest(change=change):
                values = dict(base)
                values.update(change)
                with self.assertRaises(ValueError):
                    Task(**values)

    def test_unknown_policy_fails_explicitly(self):
        with self.assertRaises(ValueError):
            choose(Task("task", 0, False, False, 2), "unknown")

    def test_untyped_output_rejected(self):
        with self.assertRaises(TypeError):
            run(Task("type", 0, False, False, 2), lambda *_: "plain text")

    def test_solver_cannot_self_approve(self):
        with self.assertRaises(ValueError):
            run(Task("vote", 0, False, False, 2),
                lambda *_: Reply("answer", "approve"))

    def test_critic_must_return_verdict(self):
        with self.assertRaises(ValueError):
            run(Task("critic", 3, False, False, 2),
                lambda *_: Reply("answer"))

    def test_smoke_covers_unresolved_outcomes_without_models(self):
        record = smoke()
        self.assertEqual(record["synthetic_cases"], 6)
        self.assertEqual(record["real_models_called"], 0)
        self.assertEqual({x["status"] for x in record["outcomes"]},
                         {"complete", "blocked", "unresolved_disagreement",
                          "rejected_by_critic"})


if __name__ == "__main__":
    unittest.main()
