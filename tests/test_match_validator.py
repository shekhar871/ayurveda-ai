from src.retrieval.match_validator import document_matches_query, filter_verified_hits
from src.retrieval.query_analyzer import analyze_query


def test_weight_loss_not_hair_loss():
    intent = analyze_query("weight loss")
    assert "Sthoulya" in intent.conditions
    hair = {
        "text": "Bhringraj promotes hair growth for Khalitya hair loss.",
        "metadata": {"topics": ["hair", "khalitya"], "conditions": ["Khalitya"], "content_type": "indication"},
    }
    weight = {
        "text": "Guggulu is used in Sthoulya for weight loss and obesity.",
        "metadata": {"topics": ["weight", "sthoulya"], "conditions": ["Sthoulya"], "content_type": "indication"},
    }
    assert document_matches_query("weight loss", intent, hair) is False
    assert document_matches_query("weight loss", intent, weight) is True


def test_unknown_query_returns_empty_after_filter():
    intent = analyze_query("xyzunknown condition")
    hits = [
        {"text": "random unrelated", "metadata": {"topics": ["hair"]}, "match_score": 0.9, "grantha": "X", "sthana": "Y", "adhyaya": 1, "shloka": 1},
    ]
    assert filter_verified_hits("xyzunknown condition", intent, hits) == []
