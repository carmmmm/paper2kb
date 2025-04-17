from src.get_hgnc_metadata import enrich_with_hgnc

def test_hgnc_metadata_enrichment():
    mentions = [{"symbol": "MTOR", "hgnc_id": "HGNC:3942"}]
    enriched = enrich_with_hgnc(mentions)
    assert "alias_symbol" in enriched[0]
    assert isinstance(enriched[0]["alias_symbol"], list)