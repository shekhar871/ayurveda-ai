from src.ingestion.text_splitter import chunk_to_envelopes, split_manuscript_blocks


def test_verse_envelope_structure():
    records = [
        {
            "text": "तत्र प्रथमे वयसि...",
            "grantha": "AshtangaHridayam",
            "sthana": "Sutrasthana",
            "adhyaya": 2,
            "shloka": 5,
            "language": "san",
        }
    ]
    envs = chunk_to_envelopes(records)
    assert len(envs) == 1
    assert envs[0].grantha == "AshtangaHridayam"
    assert envs[0].citation_address().startswith("AshtangaHridayam")


def test_split_manuscript_blocks():
    raw = "श्लोक एक॥\n\nश्लोक दो॥"
    envs = split_manuscript_blocks(raw, "TestGrantha", "Sutra", 1, "san")
    assert len(envs) >= 1
