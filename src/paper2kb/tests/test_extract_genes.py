import pytest
from unittest.mock import patch
from paper2kb.extract_genes import extract_gene_disease_mentions, load_hgnc_reference

# Automatically load HGNC reference before all tests in this module
@pytest.fixture(scope="module", autouse=True)
def load_hgnc():
    load_hgnc_reference("data/reference/hgnc_complete_set.txt")

# Sample test text that includes both valid and ambiguous gene symbols
@pytest.fixture
def test_text():
    return "The MTOR gene is associated with tubulopathy and the SET gene is not relevant. COL4A3 is also mentioned in a table."

# Test fallback extraction with mock Open Targets results
@patch("paper2kb.extract_genes.get_opentargets_diseases", return_value=["tubulopathy", "dilated cardiomyopathy"])
def test_extraction_with_fallback(mock_ot, test_text):
    mentions, skipped = extract_gene_disease_mentions(test_text, use_hybrid=True, return_skipped=True)

    assert any(m["symbol"] == "MTOR" for m in mentions)
    assert any(m["source"] == "fallback" for m in mentions)
    assert "COL4A3" in [m["symbol"] for m in mentions]
    assert all("diseases" in m for m in mentions)

# Test that common-word gene symbols like "SET" are excluded by fallback
@patch("paper2kb.extract_genes.get_opentargets_diseases", return_value=[])
def test_fallback_excludes_common_words(mock_ot):
    text = "Set was found to be critical in the process."
    mentions, skipped = extract_gene_disease_mentions(text, use_hybrid=True, return_skipped=True)

    assert "SET" not in [m["symbol"] for m in mentions]

# Test that unrecognized gene symbols are reported as skipped
def test_skipped_genes_are_reported():
    text = "XYZGENE has no HGNC match."
    mentions, skipped = extract_gene_disease_mentions(text, use_hybrid=True, return_skipped=True)

    assert "XYZGENE" in skipped
    assert mentions == []

# Test behavior when skipped genes are not requested in the return
def test_return_without_skipped():
    text = "The MTOR gene is critical in disease."
    mentions = extract_gene_disease_mentions(text, use_hybrid=False, return_skipped=False)

    assert isinstance(mentions, list)
    assert all("symbol" in m for m in mentions)