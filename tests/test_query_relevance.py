from src.retrieval.query_analyzer import analyze_query, relevance_score


def test_pitta_contraindication_intent():
    intent = analyze_query("Pitta aggravation contraindications")
    assert intent.intent == "contraindication"
    assert "Pitta aggravation" in intent.conditions


def test_pitta_beats_hair_on_relevance():
    intent = analyze_query("Pitta aggravation contraindications")
    pitta_doc = {
        "text": "Bhringraj Taila is contraindicated when Pitta is aggravated.",
        "metadata": {"topics": ["pitta", "contraindication"], "conditions": ["Pitta aggravation"], "content_type": "contraindication"},
    }
    hair_doc = {
        "text": "Bhringraj promotes hair growth for Khalitya.",
        "metadata": {"topics": ["hair", "khalitya"], "conditions": ["Khalitya"], "content_type": "indication"},
    }
    assert relevance_score(intent, pitta_doc) > relevance_score(intent, hair_doc)
