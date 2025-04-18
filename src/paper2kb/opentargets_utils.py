import requests

def get_opentargets_diseases(gene_symbol: str):
    """
    Get known disease associations for a gene symbol using Open Targets GraphQL API.

    Args:
        gene_symbol (str): Official HGNC gene symbol.

    Returns:
        list[str]: A list of lowercase disease names associated with the gene.
    """
    # Step 1: Resolve HGNC symbol to Ensembl Gene ID via HGNC REST API
    lookup_url = f"https://rest.genenames.org/fetch/symbol/{gene_symbol}"
    headers = {"Accept": "application/json"}

    try:
        res = requests.get(lookup_url, headers=headers, timeout=10)
        if res.status_code != 200:
            print(f"[ERROR] Failed to resolve symbol {gene_symbol}")
            return []

        hgnc_data = res.json()
        docs = hgnc_data.get("response", {}).get("docs", [])
        if not docs:
            print(f"[WARN] No HGNC record found for symbol {gene_symbol}")
            return []

        ensembl_id = docs[0].get("ensembl_gene_id")
        if not ensembl_id:
            print(f"[WARN] No Ensembl ID found for symbol {gene_symbol}")
            return []

    except Exception as e:
        print(f"[ERROR] Failed to resolve HGNC symbol '{gene_symbol}': {e}")
        return []

    # Step 2: Query Open Targets GraphQL API using Ensembl Gene ID
    query = """
    query getAssociations($ensemblId: String!) {
      target(ensemblId: $ensemblId) {
        associatedDiseases {
          rows {
            disease {
              name
            }
          }
        }
      }
    }
    """

    gql_url = "https://api.platform.opentargets.org/api/v4/graphql"
    try:
        response = requests.post(
            gql_url,
            json={"query": query, "variables": {"ensemblId": ensembl_id}},
            headers={"Content-Type": "application/json"},
            timeout=10
        )

        if response.status_code != 200:
            print(f"[WARN] GraphQL query failed (status {response.status_code})")
            print(response.text[:300])
            return []

        data = response.json()
        rows = data.get("data", {}).get("target", {}).get("associatedDiseases", {}).get("rows", [])
        return [row["disease"]["name"].lower() for row in rows if row.get("disease")]

    except Exception as e:
        print(f"[ERROR] Failed to query Open Targets for {ensembl_id}: {e}")
        return []