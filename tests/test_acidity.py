from src.retrieval.query_analyzer import analyze_query, is_negation_only_match


def test_acidity_is_treatment_intent():
    intent = analyze_query("acidity")
    assert intent.intent == "treatment"
    assert "Amlapitta" in intent.conditions


def test_acidity_negation_match_filtered():
    contra = "Bhringraj worsens acidity and burning when Pitta is aggravated."
    assert is_negation_only_match("acidity", contra) is True
    remedy = "Shatavari juice is indicated for Amlapitta and acidity."
    assert is_negation_only_match("acidity", remedy) is False
