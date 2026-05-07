from __future__ import annotations

import re
from collections import Counter

TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_\-]*")


def tokenize(text: str) -> list[str]:
    return [match.group(0).lower() for match in TOKEN_RE.finditer(text)]


def term_counts(text: str) -> Counter[str]:
    return Counter(tokenize(text))

