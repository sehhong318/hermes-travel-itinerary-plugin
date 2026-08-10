#!/usr/bin/env python3
"""Detect blocked or mismatched Tabelog HTML before parsing it."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path
from typing import Sequence, TextIO

_BLOCK_MARKERS = (
    "just a moment",
    "checking your browser",
    "captcha",
    "access denied",
    "temporarily blocked",
)


def classify_html(document: str, expected_title: str = "") -> str:
    """Classify a fetched page as ok, blocked, wrong_page, or invalid."""
    lowered = document.casefold()
    if any(marker in lowered for marker in _BLOCK_MARKERS):
        return "blocked"
    title_match = re.search(r"<title[^>]*>(.*?)</title>", document, re.I | re.S)
    if title_match is None or not expected_title.strip():
        return "invalid"
    title = html.unescape(re.sub(r"<[^>]+>", "", title_match.group(1))).strip()
    expected = expected_title.strip()
    canonical = re.sub(r"\s*\|\s*Tabelog\s*$", "", title, flags=re.I).strip()
    for marker in (" Reservation -", " - Restaurant Reviews", " - Reviews"):
        index = canonical.casefold().find(marker.casefold())
        if index >= 0:
            canonical = canonical[:index].strip()
            break
    if canonical.casefold() == expected.casefold():
        return "ok"
    return "wrong_page"


def main(
    argv: Sequence[str] | None = None,
    *,
    stdin: TextIO = sys.stdin,
    stdout: TextIO = sys.stdout,
) -> int:
    parser = argparse.ArgumentParser(
        description="Fail closed on blocked or mismatched Tabelog HTML."
    )
    parser.add_argument(
        "path",
        nargs="?",
        help="HTML file to inspect; omit to read UTF-8 HTML from stdin",
    )
    parser.add_argument("--expected-title", required=True)
    args = parser.parse_args(argv)

    try:
        document = (
            Path(args.path).read_text(encoding="utf-8", errors="replace")
            if args.path
            else stdin.read()
        )
        status = classify_html(document, args.expected_title)
        message = {"status": status, "expected_title": args.expected_title}
    except OSError as error:
        status = "error"
        message = {"status": status, "error": str(error)}
    json.dump(message, stdout, ensure_ascii=False)
    stdout.write("\n")
    return 0 if status == "ok" else 2


if __name__ == "__main__":
    raise SystemExit(main())
