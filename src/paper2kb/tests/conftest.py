import pytest
from pathlib import Path

@pytest.fixture
def example_text():
    return "The MTOR gene is associated with tubulopathy and dilated cardiomyopathy."

@pytest.fixture
def sample_mention():
    return {
        "symbol": "MTOR",
        "original_mention": "MTOR",
        "sentence": "The MTOR gene is associated with tubulopathy.",
        "diseases": ["tubulopathy"],
        "hgnc_id": "HGNC:3942",
        "name": "mechanistic target of rapamycin kinase",
        "alias_symbol": ["RAFT1", "RAPT1"],
        "hg38_chr": "1",
        "hg38_start": 11106535,
        "hg38_end": 11262556,
        "hg19_chr": "1",
        "hg19_start": 11166592,
        "hg19_end": 11166593,
        "normalized_diseases": [{"label": "Tubulopathy", "mondo_id": "MONDO:0012345"}]
    }