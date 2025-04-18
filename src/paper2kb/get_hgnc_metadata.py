import requests

def enrich_with_hgnc(gene_entries):
    """
    Enrich a list of gene entries with HGNC metadata.

    For each gene dictionary with a 'symbol' field, this function queries
    the HGNC REST API and adds the following fields:
      - hgnc_id (e.g., 'HGNC:1234')
      - name (official gene name)
      - alias_symbol (list of aliases)

    Args:
        gene_entries (list of dict): Each entry must include a 'symbol' key.

    Returns:
        list of dict: Gene entries with HGNC metadata fields added.
    """
    enriched = []
    for gene in gene_entries:
        symbol = gene.get('symbol')
        url = f"https://rest.genenames.org/fetch/symbol/{symbol}"
        headers = {"Accept": "application/json"}

        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                docs = data.get("response", {}).get("docs", [])
                if docs:
                    doc = docs[0]
                    aliases = doc.get("alias_symbol")
                    gene.update({
                        "hgnc_id": doc.get("hgnc_id"),
                        "name": doc.get("name"),
                        "alias_symbol": aliases if isinstance(aliases, list) else []
                    })
                else:
                    # Symbol not found in HGNC
                    gene.update({
                        "hgnc_id": None,
                        "name": None,
                        "alias_symbol": []
                    })
            else:
                # Request failed (e.g., 404 or 500)
                gene.update({
                    "hgnc_id": None,
                    "name": None,
                    "alias_symbol": []
                })
        except Exception as e:
            print(f"[WARN] Failed to fetch HGNC metadata for {symbol}: {e}")
            gene.update({
                "hgnc_id": None,
                "name": None,
                "alias_symbol": []
            })

        enriched.append(gene)

    return enriched
