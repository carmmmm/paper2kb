from src.normalize_diseases import normalize_diseases
import pytest
from unittest.mock import patch
from requests.exceptions import RequestException

@pytest.fixture
def mock_mondo_response():
    return {
        "response": {
            "docs": [{
                "label": "Tubulopathy",
                "obo_id": "MONDO:0012345"
            }]
        }
    }

@patch("src.normalize_diseases.requests.get")
def test_disease_normalization(mock_get, mock_mondo_response):
    # Configure mock to return our fake MONDO result
    mock_get.return_value.json.return_value = mock_mondo_response

    mentions = [{"diseases": ["tubulopathy"]}]
    normalized = normalize_diseases(mentions)

    assert "normalized_diseases" in normalized[0]
    assert len(normalized[0]["normalized_diseases"]) == 1
    assert normalized[0]["normalized_diseases"][0]["label"] == "Tubulopathy"
    assert normalized[0]["normalized_diseases"][0]["mondo_id"] == "MONDO:0012345"

@patch("src.normalize_diseases.requests.get")
def test_disease_not_found(mock_get):
    mock_get.return_value.json.return_value = {
        "response": {
            "docs": []
        }
    }

    mentions = [{"diseases": ["nonexistent disease"]}]
    normalized = normalize_diseases(mentions)

    result = normalized[0]["normalized_diseases"][0]
    assert result["label"] == "nonexistent disease"
    assert result["mondo_id"] is None

from requests.exceptions import RequestException

@patch("src.normalize_diseases.requests.get", side_effect=RequestException("server down"))
def test_disease_api_failure(mock_get):
    mentions = [{"diseases": ["tubulopathy"]}]
    normalized = normalize_diseases(mentions)

    result = normalized[0]["normalized_diseases"][0]
    assert result["label"] == "tubulopathy"
    assert result["mondo_id"] is None