#!/usr/bin/env python3
"""Validate grant-facing prose against frozen pilot evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from rep_audit.reporting.grant_package import validate_grant_package


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--write",
        type=Path,
        default=None,
        help="Optional path for the deterministic validation JSON.",
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    result = validate_grant_package(root)
    payload = json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    if args.write is not None:
        output = args.write if args.write.is_absolute() else root / args.write
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
