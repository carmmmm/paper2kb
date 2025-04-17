from src.get_hgnc_metadata import enrich_with_hgnc
from src.get_coordinates import add_coordinates
from src.normalize_diseases import normalize_diseases

def test_full_pipeline_no_ner():
    # Start from a fake gene mention you control
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

    assert gene["hgnc_id"] == "HGNC:3942"
    assert gene["name"].lower().startswith("mechanistic target")
    assert "hg38_chr" in gene
    assert isinstance(gene["normalized_diseases"], list)
