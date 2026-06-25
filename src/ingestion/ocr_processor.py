from __future__ import annotations

from pathlib import Path

import pytesseract
from PIL import Image

from src.ingestion.text_splitter import VerseEnvelope, split_manuscript_blocks

LANG_MAP = {
    "san": "san",
    "hin": "hin",
    "mar": "mar",
    "en": "eng",
}


def extract_text_from_image(
    image_path: str | Path,
    language: str = "san",
) -> str:
    """Run Tesseract OCR with Sanskrit/Hindi/Marathi packs when installed."""
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {path}")

    tess_lang = LANG_MAP.get(language, "san+hin+eng")
    img = Image.open(path)
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")

    config = "--psm 6 -c preserve_interword_spaces=1"
    text = pytesseract.image_to_string(img, lang=tess_lang, config=config)
    return text.strip()


async def process_manuscript_image(
    image_path: str | Path,
    grantha: str,
    sthana: str,
    adhyaya: int,
    language: str = "san",
) -> list[VerseEnvelope]:
    """OCR pipeline: image -> utf-8 text -> shloka-level envelopes."""
    raw = extract_text_from_image(image_path, language=language)
    return split_manuscript_blocks(raw, grantha, sthana, adhyaya, language=language)
