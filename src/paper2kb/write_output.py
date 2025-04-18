import json
import csv
from pathlib import Path

def save_output(data, path, fmt="json"):
    """
    Save structured output as JSON or CSV.

    Args:
        data (list[dict]): Cleaned gene-disease entries.
        path (str or Path): Output file path.
        fmt (str): 'json' or 'csv'.
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
            if isinstance(val, list):
                if all(isinstance(x, str) for x in val):
                    return "; ".join(val)
                elif all(isinstance(x, dict) and "label" in x for x in val):
                    return "; ".join(
                        f"{d['label']} ({d['mondo_id']})" if d.get("mondo_id") else d["label"]
                        for d in val
                    )
            return val

        flat_data = []
        for item in data:
            flat_data.append({k: flatten_value(v) for k, v in item.items()})

        fieldnames = flat_data[0].keys()
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(flat_data)

    else:
        raise ValueError(f"Unsupported format: {fmt}")