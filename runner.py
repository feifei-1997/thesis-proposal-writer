#!/usr/bin/env python3
"""Agent sandbox JSON entrypoint for thesis proposal preparation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from core.cqvip_client import CqvipError
from main import ThesisProposalWriter, VERSION


def read_payload(input_path: str | None) -> dict[str, Any]:
    raw = (
        Path(input_path).read_text(encoding="utf-8-sig")
        if input_path
        else sys.stdin.read().lstrip("\ufeff")
    )
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError("input JSON must be an object")
    return payload


def run_payload(
    payload: dict[str, Any], service: ThesisProposalWriter | None = None
) -> dict[str, Any]:
    return (service or ThesisProposalWriter()).execute(payload)


def failure(error_value: Any) -> dict[str, Any]:
    error_data = (
        error_value.to_dict()
        if isinstance(error_value, CqvipError)
        else {
            "code": "PROPOSAL_RUNNER_ERROR",
            "message": str(error_value),
            "retryable": False,
        }
    )
    return {
        "success": False,
        "status": "failed",
        "version": VERSION,
        "error": error_data,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare a thesis proposal from JSON")
    parser.add_argument("--input", help="UTF-8 JSON file; defaults to stdin")
    parser.add_argument("--pretty", action="store_true", help="pretty-print JSON")
    args = parser.parse_args()
    try:
        output = run_payload(read_payload(args.input))
        exit_code = 0
    except Exception as exc:  # noqa: BLE001 - JSON CLI boundary
        output = failure(exc)
        exit_code = 2
    print(json.dumps(output, ensure_ascii=False, indent=2 if args.pretty else None))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
