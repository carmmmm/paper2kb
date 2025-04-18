import pytest
from unittest.mock import patch
from paper2kb.get_hgnc_metadata import enrich_with_hgnc

@pytest.fixture
def mentions():
    return [{"symbol": "MTOR"}, {"symbol": "FAKEGENE"}]

@patch("paper2kb.get_hgnc_metadata.requests.get")
def test_enrich_success(mock_get, mentions):
    # Mock a successful response for MTOR
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "response": {
            "docs": [
                {
                    "hgnc_id": "HGNC:3942",
                    "name": "mechanistic target of rapamycin kinase",
                    "alias_symbol": ["RAFT1", "RAPT1"]
                }
            ]
        }
    }

    enriched = enrich_with_hgnc([mentions[0]])
    assert enriched[0]["hgnc_id"] == "HGNC:3942"
    assert enriched[0]["name"].lower().startswith("mechanistic")
    assert "RAFT1" in enriched[0]["alias_symbol"]

@patch("paper2kb.get_hgnc_metadata.requests.get")
def test_enrich_no_results(mock_get, mentions):
    # Simulate HGNC returning no matching docs
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "response": {"docs": []}
    }

    enriched = enrich_with_hgnc([mentions[1]])
    assert enriched[0]["hgnc_id"] is None
    assert enriched[0]["alias_symbol"] == []

@patch("paper2kb.get_hgnc_metadata.requests.get")
def test_enrich_api_error(mock_get, mentions):
    # Simulate failed API call
    mock_get.return_value.status_code = 500

    enriched = enrich_with_hgnc([mentions[0]])
    assert enriched[0]["hgnc_id"] is None
    assert enriched[0]["alias_symbol"] == []

@patch("paper2kb.get_hgnc_metadata.requests.get", side_effect=Exception("Timeout"))
def test_enrich_request_exception(mock_get, mentions):
    # Simulate a network error
    enriched = enrich_with_hgnc([mentions[0]])
    assert enriched[0]["hgnc_id"] is None
    assert enriched[0]["alias_symbol"] == []