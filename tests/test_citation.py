import re

from src.agents.citation_verifier import CITATION_PATTERN, format_citation


def test_citation_format_parses():
    cite = format_citation("AshtangaHridayam", "Sutrasthana", 2, 5)
    match = CITATION_PATTERN.search(cite)
    assert match is not None
    assert match.group("grantha") == "AshtangaHridayam"
    assert int(match.group("adhyaya")) == 2
    assert int(match.group("shloka")) == 5


def test_invalid_citation_pattern():
    assert CITATION_PATTERN.search("Random text without coordinates") is None
