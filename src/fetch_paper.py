import os
import logging
from typing import Optional
from bs4 import BeautifulSoup

from Bio import Entrez
import requests

# Set your email for NCBI Entrez
Entrez.email = os.environ.get("ENTREZ_EMAIL", "example@example.com")

def fetch_paper_text(pmid: str, prefer_fulltext: bool = True, return_source: bool = False) -> str | tuple:
    logging.info(f"📥 Attempting full-text retrieval for PMID: {pmid}")

    # Step 1: Try PubMed Central (PMC) full text via PMCID
    try:
        handle = Entrez.elink(dbfrom="pubmed", db="pmc", id=pmid, linkname="pubmed_pmc")
        records = Entrez.read(handle)
        links = records[0].get("LinkSetDb", [])
        for db in links:
            for link in db["Link"]:
                pmcid = link["Id"]
                logging.info(f"🔗 Found PMCID: {pmcid} — trying PMC full text via Entrez")
                pmc_handle = Entrez.efetch(db="pmc", id=pmcid, rettype="full", retmode="xml")
                soup = BeautifulSoup(pmc_handle, "lxml-xml")
                body = soup.find("body")
                if body:
                    full_text = body.get_text(separator="\n").strip()
                    logging.info("✅ Full text retrieved from NCBI PMC.")
                    return (full_text, "NCBI PMC full text") if return_source else full_text
    except Exception as e:
        logging.warning(f"NCBI PMC full text fetch failed: {e}")

    # Step 2: Try Europe PMC full text
    try:
        epmc_url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmid}/fullTextXML"
        response = requests.get(epmc_url)
        if response.ok and '<' in response.text:
            soup = BeautifulSoup(response.text, "lxml")
            body = soup.find("body")
            if body:
                full_text = body.get_text(separator="\n").strip()
                logging.info("✅ Full text retrieved from Europe PMC.")
                return (full_text, "Europe PMC full text") if return_source else full_text
    except Exception as e:
        logging.warning(f"Europe PMC fetch failed: {e}")

    # Step 3: Fallback to Entrez abstract
    try:
        handle = Entrez.efetch(db="pubmed", id=pmid, rettype="abstract", retmode="text")
        abstract = handle.read()
        if abstract:
            logging.info("ℹ️ Falling back to abstract via Entrez.")
            return (abstract.strip(), "Entrez abstract") if return_source else abstract.strip()
    except Exception as e:
        logging.warning(f"Entrez fetch failed: {e}")

    raise RuntimeError(f"Unable to retrieve text for PMID {pmid}")

def fetch_local_text(filepath: str) -> Optional[str]:
    """Optional dev/test helper to read a local file instead of fetching live."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"No such file: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read().strip()
