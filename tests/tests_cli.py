import subprocess
import os
import sys

CLI_PATH = os.path.join("src", "cli.py")

def test_cli_json_output(tmp_path):
    out_path = tmp_path / "cli_output.json"

    result = subprocess.run([
        sys.executable, CLI_PATH,
        "--pmid", "38790019",
        "--format", "json",
        "--output", str(out_path)
    ], capture_output=True, text=True)

    print(result.stdout)
    print(result.stderr)

    assert result.returncode == 0, "CLI exited with non-zero status"
    assert out_path.exists(), "Output file was not created"
    content = out_path.read_text()
    assert '"symbol":' in content, "Expected gene symbol not found in JSON output"

def test_cli_help_shows_usage():
    result = subprocess.run([
        sys.executable, CLI_PATH, "--help"
    ], capture_output=True, text=True)

    assert result.returncode == 0
    assert "Parse gene-disease metadata" in result.stdout