import requests
from pyliftover import LiftOver

# Initialize liftover converter for hg38 → hg19
lo = LiftOver('hg38', 'hg19')

def add_coordinates(gene_entries, build="both"):
    """
    Add genomic coordinates (hg38 and/or hg19) to a list of gene entries.

    Args:
        gene_entries (list of dict): Gene metadata, each with at least a 'symbol' key.
        build (str): One of 'hg38', 'hg19', or 'both'. Controls which coordinates to add.

    Returns:
        list of dict: Updated gene entries with coordinate fields added.
    """
    for gene in gene_entries:
        symbol = gene['symbol']
        coords = get_ensembl_coordinates(symbol)

        # Add hg38 coordinates if available
        if coords:
            if build in ['hg38', 'both']:
                gene.update({
                    "hg38_chr": coords.get("hg38_chr"),
                    "hg38_start": coords.get("hg38_start"),
                    "hg38_end": coords.get("hg38_end")
                })

            # Convert to hg19 using liftover
            if build in ['hg19', 'both'] and coords.get("hg38_chr") and coords.get("hg38_start"):
                lifted = lift_hg38_to_hg19(coords["hg38_chr"], coords["hg38_start"])
                gene.update({
                    "hg19_chr": lifted.get("hg19_chr"),
                    "hg19_start": lifted.get("hg19_start"),
                    "hg19_end": lifted.get("hg19_end")
                })
        else:
            # If coordinates are missing, fill with None placeholders
            if build in ['hg38', 'both']:
                gene.update({"hg38_chr": None, "hg38_start": None, "hg38_end": None})
            if build in ['hg19', 'both']:
                gene.update({"hg19_chr": None, "hg19_start": None, "hg19_end": None})

    return gene_entries

def get_ensembl_coordinates(symbol):
    """
    Query Ensembl REST API to get gene coordinates for hg38.

    Args:
        symbol (str): Official HGNC gene symbol.

    Returns:
        dict or None: Dictionary with 'hg38_chr', 'hg38_start', and 'hg38_end', or None if lookup fails.
    """
    try:
        response = requests.get(
            f"https://rest.ensembl.org/lookup/symbol/homo_sapiens/{symbol}?expand=1",
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        if response.status_code != 200:
            return None
        data = response.json()
        return {
            "hg38_chr": data.get("seq_region_name"),
            "hg38_start": data.get("start"),
            "hg38_end": data.get("end")
        }
    except Exception as e:
        print(f"[WARN] Failed to get Ensembl coordinates for {symbol}: {e}")
        return None

def lift_hg38_to_hg19(chrom, start):
    """
    Convert hg38 coordinates to hg19 using pyliftover.

    Args:
        chrom (str): Chromosome (e.g., '1', 'X').
        start (int): hg38 start position.

    Returns:
        dict: hg19_chr, hg19_start, hg19_end (approximate).
              Returns None values on failure.
    """
    try:
        lifted = lo.convert_coordinate(f"chr{chrom}", int(start))
        if lifted:
            hg19_chr, hg19_pos, _, _ = lifted[0]
            return {
                "hg19_chr": hg19_chr.replace("chr", ""),
                "hg19_start": int(hg19_pos),
                "hg19_end": int(hg19_pos) + 1  # Approximate length
            }
    except Exception as e:
        print(f"[WARN] LiftOver failed for chr{chrom}:{start} — {e}")

    return {
        "hg19_chr": None,
        "hg19_start": None,
        "hg19_end": None
    }