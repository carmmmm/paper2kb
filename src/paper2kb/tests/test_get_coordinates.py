import pytest
from unittest.mock import patch
from paper2kb.get_coordinates import add_coordinates

# ---------------- Fixtures ----------------

@pytest.fixture
def mentions():
    """Sample gene mention with known HGNC ID."""
    return [{"symbol": "MTOR", "hgnc_id": "HGNC:3942"}]

# ---------------- Tests ----------------

@patch("paper2kb.get_coordinates.requests.get")
def test_add_coordinates_success(mock_get, mentions):
    """
    Test successful coordinate enrichment from Ensembl with working liftover.
    """
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
    assert gene["hg19_chr"] is not None  # Confirm liftover added hg19 coordinates


@patch("paper2kb.get_coordinates.requests.get")
def test_add_coordinates_api_fail(mock_get, mentions):
    """
    If Ensembl API fails, coordinate fields should be None.
    """
    mock_get.return_value.status_code = 500

    enriched = add_coordinates(mentions.copy(), build="both")
    gene = enriched[0]

    assert gene["hg38_chr"] is None
    assert gene["hg19_chr"] is None


@patch("paper2kb.get_coordinates.requests.get")
@patch("paper2kb.get_coordinates.lo.convert_coordinate", return_value=None)
def test_liftover_fail(mock_liftover, mock_get, mentions):
    """
    Liftover failure should result in hg19 fields being None, hg38 still populated.
    """
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


@patch("paper2kb.get_coordinates.requests.get")
def test_hg38_only(mock_get, mentions):
    """
    If build is 'hg38', no hg19 coordinates should be added.
    """
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


@patch("paper2kb.get_coordinates.requests.get")
def test_empty_input(mock_get):
    """
    Empty input list should return immediately and make no API calls.
    """
    result = add_coordinates([], build="both")

    assert result == []
    mock_get.assert_not_called()