import requests

def enrich_with_hgnc(gene_entries):
    """
    Given a list of gene dicts with 'symbol', enrich with HGNC metadata:
    - hgnc_id
    - name
    - alias_symbol
    """
    enriched = []
    for gene in gene_entries:
        symbol = gene['symbol']
        url = f"https://rest.genenames.org/fetch/symbol/{symbol}"
        headers = {"Accept": "application/json"}
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                docs = data["response"]["docs"]
                if docs:
                    doc = docs[0]
                    aliases = doc.get("alias_symbol")
                    gene.update({
                        "hgnc_id": doc.get("hgnc_id"),
                        "name": doc.get("name"),
                        "alias_symbol": aliases if isinstance(aliases, list) else []
                    })
                else:
                    gene.update({"hgnc_id": None, "name": None, "alias_symbol": []})
            else:
                gene.update({"hgnc_id": None, "name": None, "alias_symbol": []})
        except Exception as e:
            print(f"[WARN] Failed to fetch HGNC for {symbol}: {e}")
            gene.update({"hgnc_id": None, "name": None, "alias_symbol": []})

        enriched.append(gene)

    return enriched