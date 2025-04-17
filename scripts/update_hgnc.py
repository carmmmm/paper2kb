import os
import requests
from datetime import datetime

HGNC_URL = "https://storage.googleapis.com/public-download-files/hgnc/tsv/tsv/hgnc_complete_set.txt"
DEST_DIR = "data/reference"
FILENAME = "hgnc_complete_set.txt"

def download_hgnc():
    os.makedirs(DEST_DIR, exist_ok=True)
    dest_path = os.path.join(DEST_DIR, FILENAME)

    print(f"[INFO] Downloading HGNC data from {HGNC_URL}")
    response = requests.get(HGNC_URL)
    response.raise_for_status()

    with open(dest_path, "w", encoding="utf-8") as f:
        f.write(response.text)

    # Optional: timestamp the update
    with open(os.path.join(DEST_DIR, "last_updated.txt"), "w") as f:
        f.write(f"Updated: {datetime.now().isoformat()}")

    print(f"[INFO] HGNC data saved to {dest_path}")


    versioned = os.path.join(DEST_DIR, f"hgnc_{datetime.now().date()}.txt")
    with open(versioned, "w") as f:
        f.write(response.text)

if __name__ == "__main__":
    download_hgnc()
