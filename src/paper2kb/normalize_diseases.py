import requests

def normalize_diseases(gene_entries):
    """
    Normalize disease names using the MONDO ontology via EMBL-EBI OLS API.

    Args:
        gene_entries (list): A list of dictionaries with a "diseases" field.

    Returns:
        list: The same list, where each entry now includes a "normalized_diseases" field.
              Each item in that list is a dict with keys: "label" and "mondo_id".
    """
    for gene in gene_entries:
        normalized = []
        for disease in gene.get("diseases", []):
            mondo = query_ols_for_disease(disease)
            if mondo:
                normalized.append(mondo)
            else:
                normalized.append({
                    "label": disease,
                    "mondo_id": None
                })
        gene["normalized_diseases"] = normalized
    return gene_entries


def query_ols_for_disease(name):
    """
    Query the EMBL-EBI Ontology Lookup Service (OLS) for MONDO-normalized disease terms.

    Args:
        name (str): Raw disease string to normalize.

    Returns:
        dict or None: A dictionary with keys 'label' and 'mondo_id', or None if not found.
    """
    try:
        res = requests.get(
            "https://www.ebi.ac.uk/ols/api/search",
            params={
                "q": name,
                "ontology": "mondo",
                "exact": "false",
                "type": "class"
            },
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
        print(f"[WARN] MONDO lookup failed for '{name}': {e}")
        return None