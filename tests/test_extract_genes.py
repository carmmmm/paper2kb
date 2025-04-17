import pytest
from unittest.mock import patch
from src.extract_genes import extract_gene_disease_mentions, load_hgnc_reference

@pytest.fixture(scope="module", autouse=True)
def load_hgnc():
    load_hgnc_reference("data/reference/hgnc_complete_set.txt")

@pytest.fixture
def test_text():
    return "The MTOR gene is associated with tubulopathy and the SET gene is not relevant. COL4A3 is also mentioned in a table."

@patch("src.extract_genes.get_opentargets_diseases", return_value=["tubulopathy", "dilated cardiomyopathy"])
def test_extraction_with_fallback(mock_ot, test_text):
    mentions, skipped = extract_gene_disease_mentions(test_text, use_hybrid=True, return_skipped=True)

    assert any(m["symbol"] == "MTOR" for m in mentions)
    assert any(m["source"] == "fallback" for m in mentions)
    assert "COL4A3" in [m["symbol"] for m in mentions]
    assert all("diseases" in m for m in mentions)

@patch("src.extract_genes.get_opentargets_diseases", return_value=[])
def test_fallback_excludes_common_words(mock_ot):
    # lowercase 'Set' shouldn't match fallback, even though it's in the gene list
    text = "Set was found to be critical in the process."
    mentions, skipped = extract_gene_disease_mentions(text, use_hybrid=True, return_skipped=True)

    assert "SET" not in [m["symbol"] for m in mentions]

def test_skipped_genes_are_reported():
    text = "XYZGENE has no HGNC match."
    mentions, skipped = extract_gene_disease_mentions(text, use_hybrid=True, return_skipped=True)

    assert "XYZGENE" in skipped
    assert mentions == []

def test_return_without_skipped():
    text = "The MTOR gene is critical in disease."
    mentions = extract_gene_disease_mentions(text, use_hybrid=False, return_skipped=False)

    assert isinstance(mentions, list)
    assert all("symbol" in m for m in mentions)