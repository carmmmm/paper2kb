import json
import csv
import pytest
from pathlib import Path
from paper2kb.write_output import save_output

@pytest.fixture
def sample_data():
    """Return a sample enriched gene entry for testing output."""
    return [
        {
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
    ]

def test_save_json_output(tmp_path, sample_data):
    """Test writing JSON output and validate structure."""
    out_path = tmp_path / "output.json"
    save_output(sample_data, out_path, fmt="json")

    assert out_path.exists()
    with open(out_path, "r", encoding="utf-8") as f:
        content = json.load(f)

    assert isinstance(content, list)
    assert content[0]["symbol"] == "MTOR"
    assert "normalized_diseases" in content[0]

def test_save_csv_output(tmp_path, sample_data):
    """Test writing CSV output and verify semicolon joins."""
    out_path = tmp_path / "output.csv"
    save_output(sample_data, out_path, fmt="csv")

    assert out_path.exists()
    with open(out_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert rows
    row = rows[0]
    assert row["symbol"] == "MTOR"
    assert "Tubulopathy" in row["normalized_diseases"]
    assert "RAFT1" in row["alias_symbol"]
    assert ";" in row["alias_symbol"]

def test_empty_data_does_not_write_file(tmp_path):
    """Test that empty input does not write a file."""
    out_path = tmp_path / "empty.json"
    save_output([], out_path, fmt="json")
    assert not out_path.exists()

def test_unsupported_format_raises(tmp_path, sample_data):
    """Ensure unsupported file types raise an error."""
    out_path = tmp_path / "invalid.txt"
    with pytest.raises(ValueError, match="Unsupported format"):
        save_output(sample_data, out_path, fmt="txt")