import json
import csv
from pathlib import Path

def save_output(data, path, fmt="json"):
    """
    Save structured gene-disease data to disk in either JSON or CSV format.

    Args:
        data (list[dict]): List of dictionaries containing enriched gene-disease info.
        path (str or Path): Output file path.
        fmt (str): Format to write ('json' or 'csv').

    Raises:
        ValueError: If the format is not one of the supported options.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if not data:
        print("[WARN] No data to write — skipping output.")
        return

    if fmt == "json":
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    elif fmt == "csv":
        def flatten_value(val):
            """
            Normalize nested values for CSV output:
            - Lists of strings are joined with '; '
            - Lists of dicts (e.g., normalized diseases) are formatted as label (MONDO)
            """
            if isinstance(val, list):
                if all(isinstance(x, str) for x in val):
                    return "; ".join(val)
                elif all(isinstance(x, dict) and "label" in x for x in val):
                    return "; ".join(
                        f"{d['label']} ({d['mondo_id']})" if d.get("mondo_id") else d["label"]
                        for d in val
                    )
            return val

        flat_data = [{k: flatten_value(v) for k, v in item.items()} for item in data]
        fieldnames = flat_data[0].keys()

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(flat_data)

    else:
        raise ValueError(f"Unsupported format: {fmt}")