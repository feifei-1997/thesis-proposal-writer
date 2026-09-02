#!/usr/bin/env python3
"""Small, dependency-free client for the CQVIP literature APIs."""

from __future__ import annotations

import json
import os
import socket
import time
from typing import Any, Callable, Iterable
from urllib import error, parse, request


DEFAULT_BASE_URL = "https://superapi.cqvip.com"
MAX_PAGE_SIZE = 10
MAX_RESPONSE_BYTES = 4 * 1024 * 1024


class CqvipError(Exception):
    """Base error exposed at the runner boundary."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        retryable: bool = False,
        http_status: int | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable
        self.http_status = http_status

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "code": self.code,
            "message": self.message,
            "retryable": self.retryable,
        }
        if self.http_status is not None:
            result["http_status"] = self.http_status
        return result


class CqvipConfigurationError(CqvipError):
    """The server-side credential or endpoint configuration is unavailable."""


class CqvipInputError(CqvipError):
    """The caller supplied an invalid search parameter."""


class CqvipHTTPError(CqvipError):
    """CQVIP returned an HTTP or network error."""


Transport = Callable[[str, dict[str, str], dict[str, Any], float], dict[str, Any]]


def _text(value: Any) -> str | None:
    if value is None:
        return None
    result = str(value).strip()
    return result or None


def _names(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        value = [value]
    result: list[str] = []
    for item in value:
        name = item.get("name") if isinstance(item, dict) else item
        name = _text(name)
        if name and name not in result:
            result.append(name)
    return result


def normalize_paper(item: dict[str, Any]) -> dict[str, Any]:
    """Keep useful citation fields and discard provider-specific bulk."""
    journal_info = item.get("journalInfo")
    if not isinstance(journal_info, dict):
        journal_info = {}
    begin_page = _text(item.get("beginPage"))
    end_page = _text(item.get("endPage"))
    pages = None
    if begin_page and end_page:
        pages = begin_page if begin_page == end_page else f"{begin_page}-{end_page}"
    elif begin_page or end_page:
        pages = begin_page or end_page

    is_pdf = item.get("isPdf")
    return {
        "id": _text(item.get("id")),
        "title": _text(item.get("title")),
        "authors": _names(item.get("authorInfo") or item.get("authors")),
        "abstract": _text(item.get("abstr") or item.get("abstract")),
        "keywords": _names(item.get("keywordInfo") or item.get("keywords")),
        "organizations": _names(item.get("organInfo") or item.get("organizations")),
        "doi": _text(item.get("doi")),
        "journal": _text(journal_info.get("name") or item.get("journal")),
        "year": item.get("year") or journal_info.get("year"),
        "volume": _text(journal_info.get("vol") or item.get("volume")),
        "issue": _text(journal_info.get("num") or item.get("issue")),
        "pages": pages,
        "language": _text(item.get("paperLanguage") or item.get("language")),
        "is_oa": item.get("isOa"),
        "has_pdf": bool(is_pdf) if is_pdf is not None else None,
    }


def _extract_items(raw: dict[str, Any]) -> tuple[list[dict[str, Any]], Any]:
    containers: list[Any] = [raw.get("data"), raw.get("result"), raw]
    list_keys = ("records", "list", "items", "papers", "rows", "data")
    items: list[Any] = []
    total = raw.get("total")
    for container in containers:
        if isinstance(container, list):
            items = container
            break
        if isinstance(container, dict):
            if total is None:
                total = container.get("total") or container.get("count")
            for key in list_keys:
                candidate = container.get(key)
                if isinstance(candidate, list):
                    items = candidate
                    break
            if items:
                break
    normalized = [normalize_paper(item) for item in items if isinstance(item, dict)]
    return normalized, total


class CqvipClient:
    """CQVIP client whose credential is supplied only by trusted runtime config."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        *,
        timeout: float = 30.0,
        max_retries: int = 2,
        transport: Transport | None = None,
    ) -> None:
        self.api_key = _text(api_key) or _text(os.getenv("CQVIP_API_KEY"))
        if not self.api_key:
            raise CqvipConfigurationError(
                "CQVIP_NOT_CONFIGURED",
                "维普 API Key 未在运行环境中配置。",
            )
        self.base_url = (
            _text(base_url) or _text(os.getenv("CQVIP_BASE_URL")) or DEFAULT_BASE_URL
        ).rstrip("/")
        parsed = parse.urlparse(self.base_url)
        if parsed.scheme != "https" or not parsed.netloc:
            raise CqvipConfigurationError(
                "CQVIP_INVALID_BASE_URL",
                "维普 API 地址必须是有效的 HTTPS 地址。",
            )
        self.timeout = max(1.0, min(float(timeout), 120.0))
        self.max_retries = max(0, min(int(max_retries), 3))
        self.transport = transport

    def _redact(self, value: Any) -> str:
        text = str(value)
        return text.replace(self.api_key, "[REDACTED]")

    def _request_once(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.transport is not None:
            try:
                result = self.transport(url, headers, payload, self.timeout)
            except CqvipError:
                raise
            except Exception as exc:  # noqa: BLE001 - injected transport boundary
                raise CqvipHTTPError(
                    "CQVIP_NETWORK_ERROR",
                    self._redact(exc),
                    retryable=True,
                ) from exc
            if not isinstance(result, dict):
                raise CqvipHTTPError(
                    "CQVIP_INVALID_RESPONSE",
                    "维普 API 返回内容不是 JSON 对象。",
                )
            return result

        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = request.Request(url, data=body, headers=headers, method="POST")
        try:
            with request.urlopen(req, timeout=self.timeout) as response:
                raw_body = response.read(MAX_RESPONSE_BYTES + 1)
                if len(raw_body) > MAX_RESPONSE_BYTES:
                    raise CqvipHTTPError(
                        "CQVIP_RESPONSE_TOO_LARGE",
                        "维普 API 返回内容超过安全限制。",
                        http_status=response.status,
                    )
                return json.loads(raw_body.decode("utf-8-sig"))
        except error.HTTPError as exc:
            response_text = exc.read(8192).decode("utf-8", errors="replace")
            retryable = exc.code == 429 or 500 <= exc.code < 600
            raise CqvipHTTPError(
                "CQVIP_HTTP_ERROR",
                self._redact(response_text or f"HTTP {exc.code}"),
                retryable=retryable,
                http_status=exc.code,
            ) from exc
        except (error.URLError, TimeoutError, socket.timeout) as exc:
            raise CqvipHTTPError(
                "CQVIP_NETWORK_ERROR",
                self._redact(exc),
                retryable=True,
            ) from exc
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CqvipHTTPError(
                "CQVIP_INVALID_RESPONSE",
                "维普 API 返回了无法解析的 JSON。",
            ) from exc

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        last_error: CqvipError | None = None
        for attempt in range(self.max_retries + 1):
            try:
                result = self._request_once(path, payload)
                if result.get("success") is False:
                    message = result.get("message") or result.get("msg") or "维普 API 请求失败。"
                    raise CqvipHTTPError(
                        "CQVIP_API_ERROR",
                        self._redact(message),
                    )
                return result
            except CqvipError as exc:
                last_error = exc
                if not exc.retryable or attempt >= self.max_retries:
                    raise
                time.sleep(0.25 * (2**attempt))
        assert last_error is not None
        raise last_error

    @staticmethod
    def _validate_query(query: Any) -> str:
        result = _text(query)
        if not result:
            raise CqvipInputError("CQVIP_QUERY_REQUIRED", "检索词不能为空。")
        if len(result) > 500:
            raise CqvipInputError(
                "CQVIP_QUERY_TOO_LONG",
                "检索词不能超过 500 个字符。",
            )
        return result

    @staticmethod
    def _validate_size(size: Any) -> int:
        try:
            result = int(size)
        except (TypeError, ValueError) as exc:
            raise CqvipInputError("CQVIP_INVALID_SIZE", "size 必须是整数。") from exc
        if not 1 <= result <= MAX_PAGE_SIZE:
            raise CqvipInputError(
                "CQVIP_INVALID_SIZE",
                f"size 必须在 1 到 {MAX_PAGE_SIZE} 之间。",
            )
        return result

    def search(
        self,
        query: str,
        *,
        mode: str = "simple",
        page: int = 1,
        size: int = 10,
    ) -> dict[str, Any]:
        query = self._validate_query(query)
        size = self._validate_size(size)
        mode = (_text(mode) or "simple").lower()
        if mode not in {"simple", "ai"}:
            raise CqvipInputError(
                "CQVIP_INVALID_MODE",
                "mode 只支持 simple 或 ai。",
            )
        try:
            page = int(page)
        except (TypeError, ValueError) as exc:
            raise CqvipInputError("CQVIP_INVALID_PAGE", "page 必须是整数。") from exc
        if page < 1:
            raise CqvipInputError("CQVIP_INVALID_PAGE", "page 必须大于等于 1。")

        if mode == "ai":
            path = "/unifiedsearch/search/v1/paper/ai-search"  # AI 检索
            payload = {"size": size, "content": query}
        else:
            path = "/unifiedsearch/search/v1/paper/simple-search"  # 普通检索
            payload = {"page": page, "size": size, "content": query}
        raw = self._post(path, payload)
        papers, total = _extract_items(raw)
        return {
            "provider": "cqvip",
            "mode": mode,
            "query": query,
            "page": page if mode == "simple" else None,
            "size": size,
            "total": total,
            "papers": papers,
            "message": _text(raw.get("message") or raw.get("msg")),
        }

    def paper_detail(self, paper_id: Any) -> dict[str, Any]:
        paper_id = _text(paper_id)
        if not paper_id:
            raise CqvipInputError("CQVIP_PAPER_ID_REQUIRED", "文献 ID 不能为空。")
        raw = self._post(
            "/unifiedsearch/search/v1/paper-detail",  # 文献详情
            {"id": paper_id},
        )
        data = raw.get("data")
        if isinstance(data, list):
            data = data[0] if data else {}
        if not isinstance(data, dict):
            data = raw.get("result") if isinstance(raw.get("result"), dict) else raw
        return {
            "provider": "cqvip",
            "paper": normalize_paper(data),
            "message": _text(raw.get("message") or raw.get("msg")),
        }

    def format_citations(
        self,
        paper_ids: Iterable[Any],
        *,
        format_type: int = 1,
    ) -> dict[str, Any]:
        ids: list[str] = []
        for value in paper_ids:
            paper_id = _text(value)
            if paper_id and paper_id not in ids:
                ids.append(paper_id)
        if not ids:
            raise CqvipInputError(
                "CQVIP_PAPER_IDS_REQUIRED",
                "至少需要一个文献 ID。",
            )
        if len(ids) > 20:
            raise CqvipInputError(
                "CQVIP_TOO_MANY_PAPER_IDS",
                "单次最多格式化 20 条文献。",
            )
        try:
            format_type = int(format_type)
        except (TypeError, ValueError) as exc:
            raise CqvipInputError(
                "CQVIP_INVALID_FORMAT_TYPE",
                "format_type 必须是整数。",
            ) from exc
        if format_type < 1:
            raise CqvipInputError(
                "CQVIP_INVALID_FORMAT_TYPE",
                "format_type 必须大于等于 1。",
            )

        raw = self._post(
            "/unifiedsearch/search/v1/bibliography-citation",  # 引用格式化
            {
                "paperDetails": [{"id": paper_id} for paper_id in ids],
                "formatType": format_type,
            },
        )
        return {
            "provider": "cqvip",
            "paper_ids": ids,
            "format_type": format_type,
            "citations": raw.get("data") if "data" in raw else raw.get("result"),
            "message": _text(raw.get("message") or raw.get("msg")),
        }
