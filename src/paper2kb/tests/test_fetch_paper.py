import pytest
from unittest.mock import patch, MagicMock
from src.fetch_paper import fetch_local_text, fetch_paper_text

# --- Local file loading ---
def test_fetch_local_text(tmp_path):
    test_file = tmp_path / "test_paper.txt"
    test_file.write_text("This is a mock test abstract.")
    text = fetch_local_text(str(test_file))
    assert "mock test abstract" in text

# --- Live test (optional) ---
@pytest.mark.integration
def test_fetch_paper_live():
    pmid = "38790019"
    text = fetch_paper_text(pmid)
    assert isinstance(text, str)
    assert len(text) > 50

# --- Fallback abstract retrieval ---
@patch("src.fetch_paper.Entrez.efetch")
def test_fetch_entrez_abstract(mock_efetch):
    mock_handle = MagicMock()
    mock_handle.read.return_value = "This is an abstract fallback."
    mock_efetch.return_value = mock_handle

    result = fetch_paper_text("99999999", prefer_fulltext=False)
    assert "abstract fallback" in result

# --- Mock EuropePMC ---
@patch("src.fetch_paper.requests.get")
def test_fetch_europepmc(mock_get):
    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.text = "<body>This is a Europe PMC full text.</body>"
    mock_get.return_value = mock_response

    text = fetch_paper_text("12345678", prefer_fulltext=True)
    assert "Europe PMC full text" in text

# --- PMC fetch via Entrez.elink and efetch ---
@patch("src.fetch_paper.Entrez.elink")
@patch("src.fetch_paper.Entrez.read")
@patch("src.fetch_paper.Entrez.efetch")
def test_fetch_pmc_fulltext(mock_efetch, mock_read, mock_elink):
    # Mock elink -> returns a fake PMCID
    mock_read.return_value = [{"LinkSetDb": [{"Link": [{"Id": "PMC123456"}]}]}]

    # Mock efetch for fulltext
    mock_efetch.return_value = MagicMock()
    mock_efetch.return_value.read.return_value = "<body>This is full PMC text</body>"

    # Use a real soup parse call for body
    with patch("src.fetch_paper.BeautifulSoup") as MockSoup:
        mock_soup = MagicMock()
        mock_soup.find.return_value.get_text.return_value = "This is full PMC text"
        MockSoup.return_value = mock_soup

        text = fetch_paper_text("99999999", return_source=False)
        assert "full PMC text" in text
