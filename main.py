#!/usr/bin/env python3
"""Workflow facade for thesis-proposal preparation and CQVIP evidence retrieval."""

from __future__ import annotations

import os
import re
from typing import Any, Callable

from core.cqvip_client import CqvipClient, CqvipError, CqvipInputError


VERSION = "1.0.0"
REQUIRED_FIELDS = (
    "degree_level",
    "major_background",
    "research_subdirection",
    "deliverable_format",
)

FIELD_ALIASES = {
    "topic": ("topic", "title", "research_topic", "论文题目", "研究题目"),
    "degree_level": ("degree_level", "degree", "学位层级", "学历层级"),
    "major_background": ("major_background", "major", "专业背景", "专业"),
    "research_subdirection": (
        "research_subdirection",
        "subdirection",
        "研究子方向",
        "具体方向",
    ),
    "deliverable_format": (
        "deliverable_format",
        "format",
        "交付格式",
        "文件格式",
    ),
}


def _clean(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (list, tuple, set)):
        value = "；".join(str(item).strip() for item in value if str(item).strip())
    result = str(value).strip()
    return result or None


def _value_from(source: dict[str, Any], field: str) -> str | None:
    for alias in FIELD_ALIASES[field]:
        value = _clean(source.get(alias))
        if value:
            return value
    return None


def normalize_brief(payload: dict[str, Any]) -> dict[str, str | None]:
    """Normalize the proposal brief supplied by the host Assistant."""
    nested = payload.get("proposal_brief")
    sources = [nested if isinstance(nested, dict) else {}, payload]
    result: dict[str, str | None] = {}
    for field in FIELD_ALIASES:
        result[field] = None
        for source in sources:
            value = _value_from(source, field)
            if value:
                result[field] = value
                break

    if not result["topic"]:
        query = _clean(payload.get("query") or payload.get("content"))
        if query:
            match = re.search(
                r"(?:研究方向|论文题目|题目)(?:是|为|：|:)?\s*([^，。；;\n]+)",
                query,
            )
            result["topic"] = _clean(match.group(1)) if match else query
    return result


def _questions(topic: str | None, missing: list[str]) -> tuple[list[dict[str, str]], str]:
    subject = topic or "你的研究题目"
    catalog = {
        "degree_level": {
            "field": "degree_level",
            "question": "请确认开题报告的学位层级：本科、专业硕士、学术硕士还是博士？",
        },
        "major_background": {
            "field": "major_background",
            "question": "你的学位专业或培养方向是什么？例如车辆工程、机械工程、自动化、计算机科学与技术。",
        },
        "research_subdirection": {
            "field": "research_subdirection",
            "question": (
                f"围绕“{subject}”，你准备聚焦哪个具体子方向？请尽量说明预测对象、数据来源、"
                "拟采用的模型或要解决的核心问题；尚未确定时也可以让我推荐。"
            ),
        },
        "deliverable_format": {
            "field": "deliverable_format",
            "question": "最终希望交付为什么格式：Markdown、Word（.docx）、LaTeX 还是 PDF？如学校有模板，也请一并提供。",
        },
    }
    questions = [catalog[field] for field in missing]
    intro = (
        "我已经加载了论文开题辅导的知识库。在正式撰写前，有几个关键信息需要确认一下，"
        "这样写出来的开题报告才能贴合你的实际情况（尤其是可行性分析和研究内容部分）："
    )
    lines = [intro, ""]
    lines.extend(f"{index}、{item['question']}" for index, item in enumerate(questions, 1))
    return questions, "\n".join(lines)


def _paper_key(paper: dict[str, Any]) -> str:
    doi = _clean(paper.get("doi"))
    if doi:
        return f"doi:{doi.lower()}"
    paper_id = _clean(paper.get("id"))
    if paper_id:
        return f"id:{paper_id}"
    title = re.sub(r"\W+", "", _clean(paper.get("title")) or "").lower()
    return f"title:{title}"


class ThesisProposalWriter:
    """Prepare a complete proposal brief and retrieve supporting CQVIP papers."""

    def __init__(
        self,
        client: CqvipClient | None = None,
        client_factory: Callable[..., CqvipClient] = CqvipClient,
    ) -> None:
        self._client = client
        self._client_factory = client_factory

    @property
    def client(self) -> CqvipClient:
        if self._client is None:
            self._client = self._client_factory()
        return self._client

    def status(self) -> dict[str, Any]:
        return {
            "skill": "thesis-proposal-writer",
            "version": VERSION,
            "cqvip": {"configured": bool(os.getenv("CQVIP_API_KEY"))},
        }

    @staticmethod
    def _queries(brief: dict[str, str | None]) -> list[dict[str, str]]:
        topic = brief["topic"] or ""
        subdirection = brief["research_subdirection"] or ""
        detailed = " ".join(part for part in (topic, subdirection) if part)
        result = [{"mode": "simple", "query": topic}]
        if detailed != topic:
            result.append({"mode": "ai", "query": f"近五年 {detailed} 相关研究"})
        else:
            result.append({"mode": "ai", "query": f"近五年 {topic} 国内外研究现状"})
        return result

    def _collect_literature(
        self,
        brief: dict[str, str | None],
        *,
        max_papers: int,
        include_citations: bool,
    ) -> dict[str, Any]:
        queries = self._queries(brief)
        papers: list[dict[str, Any]] = []
        seen: set[str] = set()
        executed: list[dict[str, Any]] = []
        try:
            for item in queries:
                result = self.client.search(
                    item["query"], mode=item["mode"], size=min(max_papers, 10)
                )
                executed.append({**item, "result_count": len(result.get("papers", []))})
                for paper in result.get("papers", []):
                    key = _paper_key(paper)
                    if key not in seen and len(papers) < max_papers:
                        seen.add(key)
                        papers.append({**paper, "source_provider": "cqvip"})

            citations = None
            citation_warning = None
            paper_ids = [paper["id"] for paper in papers if paper.get("id")]
            if include_citations and paper_ids:
                try:
                    citations = self.client.format_citations(paper_ids[:20], format_type=1)
                except CqvipError as exc:
                    citation_warning = f"维普引用格式接口暂不可用：{exc.message}"
            return {
                "status": "completed",
                "provider": "cqvip",
                "queries": executed,
                "papers": papers,
                "citations": citations,
                "warning": citation_warning,
            }
        except CqvipError as exc:
            unavailable = exc.code == "CQVIP_NOT_CONFIGURED"
            return {
                "status": "unavailable" if unavailable else "failed",
                "provider": "cqvip",
                "queries": executed,
                "papers": papers,
                "citations": None,
                "warning": (
                    "维普 API Key 尚未配置，当前不能实时检索和生成真实参考文献。"
                    if unavailable
                    else f"维普检索失败：{exc.message}"
                ),
                "error": exc.to_dict(),
            }

    def prepare_proposal(self, payload: dict[str, Any]) -> dict[str, Any]:
        brief = normalize_brief(payload)
        missing = [field for field in REQUIRED_FIELDS if not brief.get(field)]
        if not brief.get("topic"):
            missing.insert(0, "topic")
            response = "请先告诉我论文的暂定题目或研究方向，我再确认开题所需的四项关键信息。"
            questions = [{"field": "topic", "question": response}]
        else:
            questions, response = _questions(brief["topic"], missing)
        if missing:
            return {
                "success": True,
                "status": "needs_input",
                "version": VERSION,
                "proposal_brief": brief,
                "missing_fields": missing,
                "questions": questions,
                "response": response,
            }

        try:
            max_papers = max(1, min(int(payload.get("max_papers", 12)), 20))
        except (TypeError, ValueError) as exc:
            raise CqvipInputError(
                "PROPOSAL_INVALID_MAX_PAPERS", "max_papers 必须是整数。"
            ) from exc
        literature = self._collect_literature(
            brief,
            max_papers=max_papers,
            include_citations=bool(payload.get("include_citations", True)),
        )
        return {
            "success": True,
            "status": "ready_to_write",
            "version": VERSION,
            "proposal_brief": brief,
            "literature_evidence": literature,
            "required_sections": [
                "研究背景与意义",
                "国内外研究现状",
                "研究目标与主要内容",
                "拟解决的关键问题",
                "研究方法与技术路线",
                "创新点",
                "可行性分析",
                "进度安排",
                "预期成果",
                "参考文献",
            ],
            "response": "信息已完整。请基于 proposal_brief 和 literature_evidence 撰写完整开题报告；文献不足时必须明确标注，不得补造参考文献。",
        }

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        action = str(payload.get("action") or "prepare_proposal").strip().lower()
        if action in {"prepare", "prepare_proposal"}:
            return self.prepare_proposal(payload)
        if action == "status":
            return {"success": True, "status": "completed", "data": self.status()}
        if action == "literature_search":
            data = self.client.search(
                payload.get("query") or payload.get("content"),
                mode=payload.get("mode", "simple"),
                page=payload.get("page", 1),
                size=payload.get("size", 10),
            )
        elif action == "literature_detail":
            data = self.client.paper_detail(payload.get("paper_id") or payload.get("id"))
        elif action == "literature_citation":
            ids = payload.get("paper_ids") or payload.get("ids") or []
            if isinstance(ids, (str, int)):
                ids = [ids]
            data = self.client.format_citations(ids, format_type=payload.get("format_type", 1))
        else:
            raise CqvipInputError(
                "PROPOSAL_INVALID_ACTION",
                "action 只支持 prepare_proposal、status 和内部 literature_* 操作。",
            )
        return {
            "success": True,
            "status": "completed",
            "version": VERSION,
            "action": action,
            "data": data,
        }
