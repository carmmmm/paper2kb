import subprocess
import os
import sys
import pytest

CLI_PATH = os.path.join("src", "cli.py")

@pytest.mark.slow
def test_cli_json_output(tmp_path):
    """Run CLI on a known PMID and ensure JSON output is created and contains expected keys."""
    out_path = tmp_path / "cli_output.json"

    result = subprocess.run([
        sys.executable, CLI_PATH,
        "--pmid", "38790019",
        "--format", "json",
        "--output", str(out_path)
    ], capture_output=True, text=True)

    print("\n--- CLI STDOUT ---\n", result.stdout)
    print("\n--- CLI STDERR ---\n", result.stderr)

    assert result.returncode == 0, f"CLI failed: {result.stderr}"
    assert out_path.exists(), "Expected JSON output file was not created"

    content = out_path.read_text(encoding="utf-8")
    assert '"symbol":' in content, "Expected gene symbol not found in JSON output"

def test_cli_help_shows_usage():
    """Run CLI with --help and ensure help text is displayed."""
    result = subprocess.run([
        sys.executable, CLI_PATH, "--help"
    ], capture_output=True, text=True)

    assert result.returncode == 0, "CLI --help failed to run"
    assert "Parse gene-disease metadata" in result.stdout, "Help output missing description"