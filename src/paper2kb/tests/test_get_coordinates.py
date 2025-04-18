import pytest
from unittest.mock import patch
from src.get_coordinates import add_coordinates

@pytest.fixture
def mentions():
    return [{"symbol": "MTOR", "hgnc_id": "HGNC:3942"}]

@patch("src.get_coordinates.requests.get")
def test_add_coordinates_success(mock_get, mentions):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "seq_region_name": "1",
        "start": 11106535,
        "end": 11262556
    }

    enriched = add_coordinates(mentions.copy(), build="both")

    gene = enriched[0]
    assert gene["hg38_chr"] == "1"
    assert gene["hg38_start"] == 11106535
    assert gene["hg38_end"] == 11262556
    assert gene["hg19_chr"] is not None  # pyliftover must be working

@patch("src.get_coordinates.requests.get")
def test_add_coordinates_api_fail(mock_get, mentions):
    mock_get.return_value.status_code = 500

    enriched = add_coordinates(mentions.copy(), build="both")
    gene = enriched[0]
    assert gene["hg38_chr"] is None
    assert gene["hg19_chr"] is None

@patch("src.get_coordinates.requests.get")
@patch("src.get_coordinates.lo.convert_coordinate", return_value=None)
def test_liftover_fail(mock_liftover, mock_get, mentions):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "seq_region_name": "1",
        "start": 11106535,
        "end": 11262556
    }

    enriched = add_coordinates(mentions.copy(), build="both")
    gene = enriched[0]
    assert gene["hg38_chr"] == "1"
    assert gene["hg19_chr"] is None

@patch("src.get_coordinates.requests.get")
def test_hg38_only(mock_get, mentions):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "seq_region_name": "1",
        "start": 11106535,
        "end": 11262556
    }

    enriched = add_coordinates(mentions.copy(), build="hg38")
    gene = enriched[0]
    assert gene["hg38_chr"] == "1"
    assert "hg19_chr" not in gene

@patch("src.get_coordinates.requests.get")
def test_empty_input(mock_get):
    result = add_coordinates([], build="both")
    assert result == []
    mock_get.assert_not_called()
