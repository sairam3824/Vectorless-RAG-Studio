from __future__ import annotations

import re
from pathlib import Path


WHITESPACE_RE = re.compile(r"[ \t]+")
WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_\-']+")


def normalize_line(line: str) -> str:
    return WHITESPACE_RE.sub(" ", line).strip()


def normalize_block(text: str) -> str:
    lines = [normalize_line(line) for line in text.replace("\r\n", "\n").splitlines()]
    compacted: list[str] = []
    blank_seen = False
    for line in lines:
        if not line:
            if not blank_seen:
                compacted.append("")
            blank_seen = True
            continue
        compacted.append(line)
        blank_seen = False
    return "\n".join(compacted).strip()


def words(text: str) -> list[str]:
    return WORD_RE.findall(text)


def preview(text: str, max_chars: int = 280) -> str:
    cleaned = normalize_block(text).replace("\n", " ")
    if len(cleaned) <= max_chars:
        return cleaned
    return cleaned[: max_chars - 1].rstrip() + "..."


def stem_filename(filename: str) -> str:
    return Path(filename).stem.replace("_", " ").replace("-", " ").strip()
