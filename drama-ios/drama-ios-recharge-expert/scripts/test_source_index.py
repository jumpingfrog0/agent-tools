#!/usr/bin/env python3
"""Deterministic tests for source_index.py; no project build is invoked."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("source_index.py")


def run(command: list[str], cwd: Path, env: dict[str, str] | None = None) -> str:
    result = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return result.stdout


class SourceIndexTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo = Path(self.tempdir.name)
        run(["git", "init", "-q"], self.repo)
        run(["git", "config", "user.name", "Index Test"], self.repo)
        run(["git", "config", "user.email", "index@example.invalid"], self.repo)
        (self.repo / "Producer.m").write_text(
            "#define POST_NOTIFY(x) x\n- (void)send { POST_NOTIFY(kPaymentDone); }\n",
            encoding="utf-8",
        )
        (self.repo / "Consumer.m").write_text(
            "#define ADD_NOTIFY(x) x\n- (void)listen { ADD_NOTIFY(kPaymentDone); }\n// ADD_NOTIFY(kPaymentDone)\n",
            encoding="utf-8",
        )
        (self.repo / "RechargeContext.m").write_text(
            "@implementation RechargeContext\n- (void)saveTraceId { NSString *traceId = @\"t\"; }\n@end\n",
            encoding="utf-8",
        )
        env = dict(os.environ, GIT_AUTHOR_DATE="2025-01-01T00:00:00Z", GIT_COMMITTER_DATE="2025-01-01T00:00:00Z")
        run(["git", "add", "."], self.repo, env)
        run(["git", "commit", "-q", "-m", "initial payment event"], self.repo, env)
        self.baseline = run(["git", "rev-parse", "HEAD"], self.repo).strip()
        (self.repo / "Future.m").write_text("void futureOrderId(void) {}\n", encoding="utf-8")
        env = dict(os.environ, GIT_AUTHOR_DATE="2025-01-02T00:00:00Z", GIT_COMMITTER_DATE="2025-01-02T00:00:00Z")
        run(["git", "add", "."], self.repo, env)
        run(["git", "commit", "-q", "-m", "future symbol"], self.repo, env)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def commit_fixture(self, message: str, files: dict[str, str]) -> None:
        for path, content in files.items():
            candidate = self.repo / path
            candidate.parent.mkdir(parents=True, exist_ok=True)
            candidate.write_text(content, encoding="utf-8")
        run(["git", "add", "."], self.repo)
        run(["git", "commit", "-q", "-m", message], self.repo)

    def index(
        self,
        *queries: str,
        revision: str | None = None,
        history_limit: int | None = None,
        include_name_similarity: bool = False,
        max_results: int | None = None,
        max_chars: int | None = None,
    ) -> tuple[str, dict]:
        command = ["python3", str(SCRIPT), "--repo", str(self.repo)]
        if revision:
            command.extend(["--rev", revision])
        if history_limit is not None:
            command.extend(["--history-limit", str(history_limit)])
        if include_name_similarity:
            command.append("--include-name-similarity")
        if max_results is not None:
            command.extend(["--max-results", str(max_results)])
        if max_chars is not None:
            command.extend(["--max-chars", str(max_chars)])
        for query in queries:
            command.extend(["--query", query])
        output = run(command, self.repo)
        return output, json.loads(output)

    def test_output_is_stable_and_roles_are_separate(self) -> None:
        first, parsed = self.index("kPaymentDone")
        second, _ = self.index("kPaymentDone")
        self.assertEqual(first, second)
        roles = {item["role"] for item in parsed["event_evidence"]}
        self.assertEqual(roles, {"consumer", "producer"})
        self.assertFalse(any(item["content"].startswith("//") for item in parsed["event_evidence"]))
        self.assertTrue(all(item["path"] for item in parsed["exact_matches"]))
        self.assertTrue(all(not Path(item["path"]).is_absolute() for item in parsed["exact_matches"]))
        self.assertTrue(all(item["symbol"] for item in parsed["exact_matches"]))
        self.assertTrue(all(item["source_identity"].startswith(item["path"]) for item in parsed["exact_matches"]))
        self.assertEqual(parsed["run_metadata"]["repository_identity"], ".")
        self.assertEqual(parsed["repository"], ".")
        serialized = json.dumps(parsed, ensure_ascii=False, sort_keys=True)
        self.assertNotIn(str(self.repo), serialized)
        self.assertNotRegex(serialized, r'"/(?:Users|private|tmp|var)/')
        self.assertEqual(
            parsed["run_metadata"]["source_revision"],
            run(["git", "rev-parse", "HEAD"], self.repo).strip(),
        )

    def test_input_query_order_is_stable(self) -> None:
        first, _ = self.index("RechargeContext", "kPaymentDone")
        second, _ = self.index("kPaymentDone", "RechargeContext")
        self.assertEqual(first, second)

    def test_revision_excludes_future_knowledge(self) -> None:
        _, parsed = self.index("futureOrderId", revision=self.baseline)
        self.assertEqual(parsed["exact_matches"], [])
        self.assertEqual(parsed["revision"], self.baseline)

    def test_default_contains_only_exact_and_event_evidence(self) -> None:
        _, parsed = self.index("RechargeContext")
        self.assertEqual(
            parsed["run_metadata"]["evidence_categories"],
            ["exact_matches", "event_evidence"],
        )
        self.assertEqual(parsed["historical_cochange"], [])
        self.assertEqual(parsed["name_similarity"], [])

    def test_low_confidence_and_limitations_cannot_block(self) -> None:
        _, parsed = self.index(
            "RechargeContext",
            history_limit=10,
            include_name_similarity=True,
        )
        self.assertTrue(all(item["confidence"] == "low" for item in parsed["name_similarity"]))
        self.assertIn("Static search cannot prove", " ".join(parsed["limitations"]))
        self.assertTrue(all(item["confidence"] == "investigation_lead_only" for item in parsed["historical_cochange"]))

    def test_result_limit_reports_deterministic_truncation(self) -> None:
        first, parsed = self.index("kPaymentDone", max_results=1)
        second, _ = self.index("kPaymentDone", max_results=1)
        self.assertEqual(first, second)
        self.assertTrue(parsed["truncated"])
        exact_counts = parsed["run_metadata"]["category_counts"]["exact_matches"]
        self.assertEqual(exact_counts["returned"], 1)
        self.assertGreater(exact_counts["found"], exact_counts["returned"])

    def test_query_strata_do_not_starve_each_other(self) -> None:
        self.commit_fixture(
            "query strata",
            {
                "AHeavy.m": "\n".join(f"void alphaNeedle{i}(void) {{ /* alphaNeedle */ }}" for i in range(8)) + "\n",
                "ZLight.m": "void betaNeedle(void) {}\n",
            },
        )
        _, parsed = self.index("alphaNeedle", "betaNeedle", max_results=2)
        self.assertEqual({item["query"] for item in parsed["exact_matches"]}, {"alphaNeedle", "betaNeedle"})
        self.assertFalse(parsed["run_metadata"]["category_counts"]["exact_matches"]["coverage_unmet"])

    def test_character_budget_covers_each_query_before_repeats(self) -> None:
        self.commit_fixture(
            "coverage first queries",
            {
                "AlphaConsumer.m": "- (void)listen { ADD_NOTIFY(queryAlpha); }\n",
                "AlphaDeclaration.h": "EXTERN_KEY(queryAlpha);\n",
                "AlphaProducer.m": "- (void)send { POST_NOTIFY(queryAlpha); }\n",
                "BetaProducer.m": f"- (void)send {{ POST_NOTIFY(queryBeta); /* {'b' * 260} */ }}\n",
            },
        )
        _, full = self.index("queryAlpha", "queryBeta")
        alpha = min(
            (item for item in full["event_evidence"] if item["query"] == "queryAlpha"),
            key=lambda item: len(json.dumps(item, ensure_ascii=False, sort_keys=True)),
        )
        beta = min(
            (item for item in full["event_evidence"] if item["query"] == "queryBeta"),
            key=lambda item: len(json.dumps(item, ensure_ascii=False, sort_keys=True)),
        )
        budget = sum(len(json.dumps(item, ensure_ascii=False, sort_keys=True)) for item in (alpha, beta))
        first, parsed = self.index("queryAlpha", "queryBeta", max_chars=budget)
        second, _ = self.index("queryBeta", "queryAlpha", max_chars=budget)
        self.assertEqual(first, second)
        self.assertEqual({item["query"] for item in parsed["event_evidence"]}, {"queryAlpha", "queryBeta"})

    def test_character_budget_covers_each_event_role_before_repeats(self) -> None:
        self.commit_fixture(
            "coverage first roles",
            {
                "RoleConsumer.m": "- (void)listen { ADD_NOTIFY(roleNeedle); }\n",
                "RoleDeclaration.h": f"EXTERN_KEY(roleNeedle); /* {'d' * 120} */\n",
                "RoleProducer.m": f"- (void)send {{ POST_NOTIFY(roleNeedle); /* {'p' * 180} */ }}\n",
                "RoleProducerTwo.m": "- (void)sendAgain { POST_NOTIFY(roleNeedle); }\n",
            },
        )
        _, full = self.index("roleNeedle")
        shortest_by_role = {
            role: min(
                (item for item in full["event_evidence"] if item["role"] == role),
                key=lambda item: len(json.dumps(item, ensure_ascii=False, sort_keys=True)),
            )
            for role in {item["role"] for item in full["event_evidence"]}
        }
        budget = sum(len(json.dumps(item, ensure_ascii=False, sort_keys=True)) for item in shortest_by_role.values())
        _, parsed = self.index("roleNeedle", max_results=len(shortest_by_role), max_chars=budget)
        self.assertEqual({item["role"] for item in parsed["event_evidence"]}, set(shortest_by_role))

    def test_character_budget_covers_each_event_path_before_repeats(self) -> None:
        self.commit_fixture(
            "coverage first paths",
            {
                "Paths/A.m": "- (void)sendA { POST_NOTIFY(pathEvent); }\n- (void)sendAAgain { POST_NOTIFY(pathEvent); }\n",
                "Paths/B.m": f"- (void)sendB {{ POST_NOTIFY(pathEvent); /* {'b' * 140} */ }}\n",
                "Paths/C.m": f"- (void)sendC {{ POST_NOTIFY(pathEvent); /* {'c' * 200} */ }}\n",
            },
        )
        _, full = self.index("pathEvent")
        producers = [item for item in full["event_evidence"] if item["role"] == "producer"]
        shortest_by_path = {
            path: min(
                (item for item in producers if item["path"] == path),
                key=lambda item: len(json.dumps(item, ensure_ascii=False, sort_keys=True)),
            )
            for path in {item["path"] for item in producers}
        }
        budget = sum(len(json.dumps(item, ensure_ascii=False, sort_keys=True)) for item in shortest_by_path.values())
        _, parsed = self.index("pathEvent", max_results=len(shortest_by_path), max_chars=budget)
        returned_paths = {item["path"] for item in parsed["event_evidence"] if item["role"] == "producer"}
        self.assertEqual(returned_paths, set(shortest_by_path))

    def test_realistic_two_event_queries_fit_under_1200(self) -> None:
        padding = "x" * 180
        self.commit_fixture(
            "realistic event budget",
            {
                "AConsumer.m": f"- (void)listen {{ ADD_NOTIFY(eventAlpha); /* {padding} */ }}\n",
                "ADeclaration.h": f"EXTERN_KEY(eventAlpha); /* {padding} */\n",
                "AProducer.m": f"- (void)send {{ POST_NOTIFY(eventAlpha); /* {padding} */ }}\n",
                "BConsumer.m": f"- (void)listen {{ ADD_NOTIFY(eventBeta); /* {padding} */ }}\n",
                "BProducer.m": f"- (void)send {{ POST_NOTIFY(eventBeta); /* {padding} */ }}\n",
            },
        )
        _, parsed = self.index("eventAlpha", "eventBeta", max_results=60, max_chars=1200)
        self.assertEqual({item["query"] for item in parsed["event_evidence"]}, {"eventAlpha", "eventBeta"})

    def test_event_role_strata_keep_producer_and_consumer(self) -> None:
        _, parsed = self.index("kPaymentDone", max_results=2)
        self.assertEqual({item["role"] for item in parsed["event_evidence"]}, {"producer", "consumer"})
        strata = parsed["run_metadata"]["category_counts"]["event_evidence"]["strata"]
        self.assertEqual({item["role"] for item in strata}, {"producer", "consumer"})
        self.assertTrue(all(item["returned"] == 1 for item in strata))

    def test_partial_path_budget_reports_uncovered_event_path(self) -> None:
        self.commit_fixture(
            "second producer path",
            {"ProducerTwo.m": "- (void)sendAgain { POST_NOTIFY(kPaymentDone); }\n"},
        )
        _, parsed = self.index("kPaymentDone", max_results=2)
        counts = parsed["run_metadata"]["category_counts"]["event_evidence"]
        producer = next(item for item in counts["strata"] if item["role"] == "producer")
        self.assertFalse(producer["coverage_met"])
        self.assertEqual(len(producer["uncovered_paths"]), 1)
        self.assertEqual(
            [item["path"] for item in counts["uncovered_strata"] if item["role"] == "producer"],
            producer["uncovered_paths"],
        )
        self.assertTrue(parsed["coverage_unmet"])

    def test_path_round_robin_preserves_diversity(self) -> None:
        self.commit_fixture(
            "path diversity",
            {
                "Many/A.m": "\n".join(f"void pathNeedleA{i}(void) {{ /* pathNeedle */ }}" for i in range(5)) + "\n",
                "One/B.m": "void pathNeedleB(void) { /* pathNeedle */ }\n",
            },
        )
        _, parsed = self.index("pathNeedle", max_results=2)
        self.assertEqual({item["path"] for item in parsed["exact_matches"]}, {"Many/A.m", "One/B.m"})
        paths = parsed["run_metadata"]["category_counts"]["exact_matches"]["strata"][0]["paths"]
        self.assertEqual({item["path"] for item in paths if item["returned"]}, {"Many/A.m", "One/B.m"})

    def test_oversized_item_does_not_starve_later_item(self) -> None:
        self.commit_fixture(
            "oversized evidence",
            {
                "A-Oversized.m": f"void budgetNeedle(void) {{ /* {'x' * 4000} */ }}\n",
                "B-Small.m": "void budgetNeedleSmall(void) { /* budgetNeedle */ }\n",
            },
        )
        _, full = self.index("budgetNeedle")
        small = next(item for item in full["exact_matches"] if item["path"] == "B-Small.m")
        small_chars = len(json.dumps(small, ensure_ascii=False, sort_keys=True))
        _, parsed = self.index("budgetNeedle", max_chars=small_chars)
        self.assertEqual([item["path"] for item in parsed["exact_matches"]], ["B-Small.m"])
        self.assertTrue(parsed["truncated"])

    def test_character_budget_reports_uncovered_strata(self) -> None:
        self.commit_fixture(
            "coverage budget",
            {
                "Alpha.m": "void coverageAlpha(void) {}\n",
                "Beta.m": "void coverageBeta(void) {}\n",
            },
        )
        _, full = self.index("coverageAlpha", "coverageBeta")
        sizes = [len(json.dumps(item, ensure_ascii=False, sort_keys=True)) for item in full["exact_matches"]]
        _, parsed = self.index("coverageAlpha", "coverageBeta", max_chars=max(sizes))
        counts = parsed["run_metadata"]["category_counts"]["exact_matches"]
        self.assertTrue(counts["coverage_unmet"])
        self.assertEqual(len(counts["uncovered_strata"]), 1)
        self.assertIn("path", counts["uncovered_strata"][0])
        self.assertTrue(parsed["coverage_unmet"])
        self.assertIn("exact_matches", parsed["uncovered_strata"])

    def test_character_limit_reports_truncation(self) -> None:
        _, parsed = self.index("kPaymentDone", max_chars=1)
        exact_counts = parsed["run_metadata"]["category_counts"]["exact_matches"]
        self.assertTrue(exact_counts["truncated"])
        self.assertEqual(exact_counts["returned"], 0)
        self.assertTrue(exact_counts["coverage_unmet"])
        self.assertTrue(all(item["query"] == "kPaymentDone" and item["path"] for item in exact_counts["uncovered_strata"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
