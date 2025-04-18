import requests

def get_opentargets_diseases(gene_symbol: str):
    # Step 1: Resolve symbol to Ensembl ID
    lookup_url = f"https://rest.genenames.org/fetch/symbol/{gene_symbol}"
    headers = {"Accept": "application/json"}
    try:
        res = requests.get(lookup_url, headers=headers, timeout=10)
        if res.status_code != 200:
            print(f"❌ Failed to resolve symbol {gene_symbol}")
            return []
        hgnc_data = res.json()
        ensembl_id = hgnc_data["response"]["docs"][0].get("ensembl_gene_id")
        if not ensembl_id:
            print(f"❌ No Ensembl ID for symbol {gene_symbol}")
            return []
    except Exception as e:
        print(f"❌ Error resolving symbol: {e}")
        return []

    # Step 2: Query Open Targets with Ensembl ID
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
            print(f"⚠️ GraphQL query failed with status {response.status_code}")
            print(response.text[:300])
            return []
        data = response.json()
        rows = data.get("data", {}).get("target", {}).get("associatedDiseases", {}).get("rows", [])
        return [row["disease"]["name"].lower() for row in rows if row.get("disease")]
    except Exception as e:
        print(f"⚠️ Error querying Open Targets: {e}")
        return []
