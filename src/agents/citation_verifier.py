from __future__ import annotations

import re

from typing import Any

CITATION_PATTERN = re.compile(
    r"(?P<grantha>[A-Za-z]+)\s*\|\s*(?P<sthana>[A-Za-z]+)\s*\|\s*"
    r"(?:Adhyaya|Chapter)\s*(?P<adhyaya>\d+)\s*\|\s*(?:Shloka|Verse)\s*(?P<shloka>\d+)",
    re.IGNORECASE,
)


async def verify_citation_string(postgres: Any, citation: str) -> bool:
    match = CITATION_PATTERN.search(citation)
    if not match:
        return False
    return await postgres.validate_citation(
        grantha=match.group("grantha"),
        sthana=match.group("sthana"),
        adhyaya=int(match.group("adhyaya")),
        shloka=int(match.group("shloka")),
    )


async def validate_remedy_citations(
    postgres: Any,
    citations: list[str],
) -> tuple[list[str], list[str]]:
    valid, invalid = [], []
    for cite in citations:
        if await verify_citation_string(postgres, cite):
            valid.append(cite)
        else:
            invalid.append(cite)
    return valid, invalid


def format_citation(grantha: str, sthana: str, adhyaya: int, shloka: int) -> str:
    return f"{grantha} | {sthana} | Adhyaya {adhyaya} | Shloka {shloka}"
