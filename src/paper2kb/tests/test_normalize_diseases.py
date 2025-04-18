import pytest
from unittest.mock import patch
from requests.exceptions import RequestException
from paper2kb.normalize_diseases import normalize_diseases

@pytest.fixture
def mock_mondo_response():
    """Fake MONDO response for 'tubulopathy'."""
    return {
        "response": {
            "docs": [{
                "label": "Tubulopathy",
                "obo_id": "MONDO:0012345"
            }]
        }
    }

@patch("paper2kb.normalize_diseases.requests.get")
def test_disease_normalization_success(mock_get, mock_mondo_response):
    """Test that a known disease gets normalized with correct MONDO ID."""
    mock_get.return_value.json.return_value = mock_mondo_response

    mentions = [{"diseases": ["tubulopathy"]}]
    normalized = normalize_diseases(mentions)

    assert "normalized_diseases" in normalized[0]
    result = normalized[0]["normalized_diseases"][0]
    assert result["label"] == "Tubulopathy"
    assert result["mondo_id"] == "MONDO:0012345"

@patch("paper2kb.normalize_diseases.requests.get")
def test_disease_not_found(mock_get):
    """Test fallback behavior when MONDO returns no matches."""
    mock_get.return_value.json.return_value = {"response": {"docs": []}}

    mentions = [{"diseases": ["unknown condition"]}]
    normalized = normalize_diseases(mentions)

    result = normalized[0]["normalized_diseases"][0]
    assert result["label"] == "unknown condition"
    assert result["mondo_id"] is None

@patch("paper2kb.normalize_diseases.requests.get", side_effect=RequestException("server down"))
def test_disease_api_failure(mock_get):
    """Test graceful handling of request exceptions (e.g., timeout, server errors)."""
    mentions = [{"diseases": ["tubulopathy"]}]
    normalized = normalize_diseases(mentions)

    result = normalized[0]["normalized_diseases"][0]
    assert result["label"] == "tubulopathy"
    assert result["mondo_id"] is None

def test_empty_disease_list():
    """Test input with no disease strings at all."""
    mentions = [{"diseases": []}]
    normalized = normalize_diseases(mentions)

    assert normalized[0]["normalized_diseases"] == []