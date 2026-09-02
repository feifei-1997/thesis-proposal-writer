import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT))

from core.cqvip_client import CqvipConfigurationError  # noqa: E402
from main import ThesisProposalWriter  # noqa: E402
from runner import run_payload  # noqa: E402


COMPLETE_BRIEF = {
    "topic": "基于深度学习的电池包寿命研究",
    "degree_level": "专业硕士",
    "major_background": "车辆工程",
    "research_subdirection": "融合工况与温度特征的电池包RUL预测",
    "deliverable_format": "Markdown",
}


class FakeClient:
    def __init__(self):
        self.search_calls = []
        self.citation_calls = []

    def search(self, query, *, mode="simple", page=1, size=10):
        self.search_calls.append({"query": query, "mode": mode, "size": size})
        suffix = "1" if mode == "simple" else "2"
        return {
            "papers": [
                {
                    "id": f"paper-{suffix}",
                    "title": f"电池包寿命预测研究{suffix}",
                    "authors": ["测试作者"],
                    "journal": "测试期刊",
                    "year": 2025,
                    "doi": "10.1/shared" if mode == "ai" else None,
                },
                {
                    "id": "duplicate",
                    "title": "重复论文",
                    "authors": ["作者乙"],
                    "doi": "10.1/shared",
                },
            ]
        }

    def format_citations(self, paper_ids, *, format_type=1):
        self.citation_calls.append(list(paper_ids))
        return {"citations": ["维普返回的引用"], "format_type": format_type}


class ProposalSkillTests(unittest.TestCase):
    def test_first_turn_returns_four_assistant_questions(self):
        output = run_payload(
            {"query": "帮我写一个开题报告，研究方向是基于深度学习的电池包寿命的研究"}
        )
        self.assertEqual(output["status"], "needs_input")
        self.assertEqual(len(output["questions"]), 4)
        self.assertIn("学位层级", output["response"])
        self.assertIn("专业", output["response"])
        self.assertIn("具体子方向", output["response"])
        self.assertIn("交付", output["response"])

    def test_only_missing_fields_are_asked(self):
        brief = dict(COMPLETE_BRIEF)
        brief.pop("deliverable_format")
        output = run_payload({"proposal_brief": brief})
        self.assertEqual(output["missing_fields"], ["deliverable_format"])
        self.assertEqual(len(output["questions"]), 1)

    def test_complete_brief_searches_cqvip_and_is_ready(self):
        client = FakeClient()
        service = ThesisProposalWriter(client=client)
        output = run_payload({"proposal_brief": COMPLETE_BRIEF}, service=service)
        self.assertEqual(output["status"], "ready_to_write")
        self.assertEqual(output["literature_evidence"]["status"], "completed")
        self.assertEqual(len(client.search_calls), 2)
        self.assertEqual({call["mode"] for call in client.search_calls}, {"simple", "ai"})
        dois = [paper.get("doi") for paper in output["literature_evidence"]["papers"]]
        self.assertEqual(dois.count("10.1/shared"), 1)
        self.assertTrue(client.citation_calls)

    def test_missing_key_does_not_fabricate_or_block_non_citation_sections(self):
        def unavailable_client_factory():
            raise CqvipConfigurationError(
                "CQVIP_NOT_CONFIGURED", "维普 API Key 未在运行环境中配置。"
            )

        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("CQVIP_API_KEY", None)
            service = ThesisProposalWriter(client_factory=unavailable_client_factory)
            output = run_payload({"proposal_brief": COMPLETE_BRIEF}, service=service)
        self.assertEqual(output["status"], "ready_to_write")
        self.assertEqual(output["literature_evidence"]["status"], "unavailable")
        self.assertEqual(output["literature_evidence"]["papers"], [])
        self.assertIn("不得补造", output["response"])

    def test_status_never_returns_api_key(self):
        with patch.dict(os.environ, {"CQVIP_API_KEY": "private-key"}):
            output = ThesisProposalWriter().execute({"action": "status"})
        self.assertNotIn("private-key", json.dumps(output, ensure_ascii=False))
        self.assertTrue(output["data"]["cqvip"]["configured"])

    def test_cli_first_turn_exits_successfully_without_key(self):
        environment = dict(os.environ)
        environment.pop("CQVIP_API_KEY", None)
        completed = subprocess.run(
            [sys.executable, str(SKILL_ROOT / "runner.py")],
            input=json.dumps({"query": "研究方向是电池包寿命预测"}, ensure_ascii=False),
            text=True,
            encoding="utf-8",
            capture_output=True,
            cwd=SKILL_ROOT,
            env=environment,
            check=False,
        )
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(json.loads(completed.stdout)["status"], "needs_input")


if __name__ == "__main__":
    unittest.main()
