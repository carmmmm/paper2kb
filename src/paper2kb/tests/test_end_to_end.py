from paper2kb.get_hgnc_metadata import enrich_with_hgnc
from paper2kb.get_coordinates import add_coordinates
from paper2kb.normalize_diseases import normalize_diseases

def test_full_pipeline_no_ner():
    """
    End-to-end integration test that starts from a manually defined gene mention.
    It validates HGNC metadata enrichment, coordinate resolution, and disease normalization.
    Useful for checking fallback or CLI-mode workflows where NER is bypassed.
    """
    mentions = [{
        "symbol": "MTOR",
        "hgnc_id": "HGNC:3942",
        "diseases": ["tubulopathy", "dilated cardiomyopathy"]
    }]

    enriched = enrich_with_hgnc(mentions)
    enriched = add_coordinates(enriched)
    enriched = normalize_diseases(enriched)

    assert len(enriched) == 1
    gene = enriched[0]

    # Validate expected HGNC metadata
    assert gene["hgnc_id"] == "HGNC:3942"
    assert gene["name"].lower().startswith("mechanistic target")

    # Validate coordinate enrichment
    assert "hg38_chr" in gene

    # Validate MONDO disease normalization
    assert isinstance(gene["normalized_diseases"], list)
    assert all("label" in d for d in gene["normalized_diseases"])