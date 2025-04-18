import requests
from pyliftover import LiftOver

# Initialize liftover once
lo = LiftOver('hg38', 'hg19')


def add_coordinates(gene_entries, build="both"):
    """
    Given a list of gene dicts with 'symbol', add:
    - hg38 coordinates (chromosome, start, end)
    - hg19 coordinates (via liftOver if available)
    If build is 'hg38', 'hg19', or 'both'
    """
    for gene in gene_entries:
        symbol = gene['symbol']
        coords = get_ensembl_coordinates(symbol)

        if coords:
            if build in ['hg38', 'both']:
                gene.update({
                    "hg38_chr": coords.get("hg38_chr"),
                    "hg38_start": coords.get("hg38_start"),
                    "hg38_end": coords.get("hg38_end")
                })
            if build in ['hg19', 'both'] and coords.get("hg38_chr") and coords.get("hg38_start"):
                lifted = lift_hg38_to_hg19(coords.get("hg38_chr"), coords.get("hg38_start"))
                gene.update({
                    "hg19_chr": lifted.get("hg19_chr"),
                    "hg19_start": lifted.get("hg19_start"),
                    "hg19_end": lifted.get("hg19_end")
                })
        else:
            if build in ['hg38', 'both']:
                gene.update({"hg38_chr": None, "hg38_start": None, "hg38_end": None})
            if build in ['hg19', 'both']:
                gene.update({"hg19_chr": None, "hg19_start": None, "hg19_end": None})

    return gene_entries


def get_ensembl_coordinates(symbol):
    """
    Query Ensembl REST API for gene coordinates (hg38).
    """
    try:
        res = requests.get(
            f"https://rest.ensembl.org/lookup/symbol/homo_sapiens/{symbol}?expand=1",
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        if res.status_code != 200:
            return None
        data = res.json()
        return {
            "hg38_chr": data.get("seq_region_name"),
            "hg38_start": data.get("start"),
            "hg38_end": data.get("end")
        }
    except Exception as e:
        print(f"[WARN] Failed to get Ensembl coords for {symbol}: {e}")
        return None


def lift_hg38_to_hg19(chrom, start):
    """
    Use pyliftover to convert hg38 to hg19 coordinates.
    """
    try:
        lifted = lo.convert_coordinate(f"chr{chrom}", int(start))
        if lifted:
            hg19_chr, hg19_pos, _, _ = lifted[0]
            return {
                "hg19_chr": hg19_chr.replace("chr", ""),
                "hg19_start": int(hg19_pos),
                "hg19_end": int(hg19_pos) + 1  # Approximate
            }
    except Exception as e:
        print(f"[WARN] LiftOver failed for chr{chrom}:{start} — {e}")
    return {"hg19_chr": None, "hg19_start": None, "hg19_end": None}
