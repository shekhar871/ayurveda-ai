from src.agents.rag_compliance import run_rag_compliance_agent


def test_rag_compliance_agent():
    mock_context = ["Bhringraj is traditionally used to promote thick hair growth."]
    hallucinated_completion = "Bhringraj treats severe acute migraine headaches instantly."

    validated_response = run_rag_compliance_agent(hallucinated_completion, mock_context)
    assert validated_response == "No information found in our knowledge base"


def test_rag_compliance_allows_grounded_text():
    mock_context = ["Bhringraj is traditionally used to promote thick hair growth."]
    grounded = "Bhringraj is traditionally used to promote thick hair growth."
    validated = run_rag_compliance_agent(grounded, mock_context)
    assert "Bhringraj" in validated
