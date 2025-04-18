import requests

def normalize_diseases(gene_entries):
    """
    For each disease string in each gene entry, look up MONDO normalization.
    Adds:
    - normalized_diseases: list of dicts with 'label' and 'mondo_id'
    """
    for gene in gene_entries:
        normalized = []
        for disease in gene.get("diseases", []):
            mondo = query_ols_for_disease(disease)
            if mondo:
                normalized.append(mondo)
            else:
                normalized.append({"label": disease, "mondo_id": None})
        gene["normalized_diseases"] = normalized
    return gene_entries


def query_ols_for_disease(name):
    """
    Use EMBL-EBI OLS (Ontology Lookup Service) to search MONDO terms.
    """
    try:
        res = requests.get(
            "https://www.ebi.ac.uk/ols/api/search",
            params={"q": name, "ontology": "mondo", "exact": "false", "type": "class"},
            headers={"Accept": "application/json"},
            timeout=10
        )
        results = res.json().get("response", {}).get("docs", [])
        if not results:
            return None
        top = results[0]
        return {
            "label": top.get("label"),
            "mondo_id": top.get("obo_id")
        }
    except Exception as e:
        print(f"[WARN] MONDO lookup failed for {name}: {e}")
        return None
