from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class VerseEnvelope:
    text: str
    grantha: str
    sthana: str
    adhyaya: int
    shloka: int
    language: str = "san"
    metadata: dict[str, Any] = field(default_factory=dict)

    def citation_address(self) -> str:
        return f"{self.grantha} | {self.sthana} | Adhyaya {self.adhyaya} | Shloka {self.shloka}"

    def to_payload(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "metadata": {
                "grantha": self.grantha,
                "sthana": self.sthana,
                "adhyaya": self.adhyaya,
                "shloka": self.shloka,
                "language": self.language,
                **self.metadata,
            },
        }


def chunk_to_envelopes(records: list[dict[str, Any]]) -> list[VerseEnvelope]:
    """Map raw verse records into structured shloka-level envelopes."""
    envelopes: list[VerseEnvelope] = []
    for rec in records:
        envelopes.append(
            VerseEnvelope(
                text=rec["text"].strip(),
                grantha=rec["grantha"],
                sthana=rec["sthana"],
                adhyaya=int(rec["adhyaya"]),
                shloka=int(rec["shloka"]),
                language=rec.get("language", "san"),
                metadata={k: v for k, v in rec.items() if k not in {"text", "grantha", "sthana", "adhyaya", "shloka", "language"}},
            )
        )
    return envelopes


def split_manuscript_blocks(
    raw_text: str,
    grantha: str,
    sthana: str,
    adhyaya: int,
    language: str = "san",
) -> list[VerseEnvelope]:
    """Split OCR output on verse delimiters (॥ or double newline)."""
    import re

    blocks = re.split(r"(?:॥\s*|\n\n+)", raw_text)
    envelopes: list[VerseEnvelope] = []
    shloka = 1
    for block in blocks:
        text = block.strip()
        if len(text) < 8:
            continue
        envelopes.append(
            VerseEnvelope(
                text=text,
                grantha=grantha,
                sthana=sthana,
                adhyaya=adhyaya,
                shloka=shloka,
                language=language,
            )
        )
        shloka += 1
    return envelopes
