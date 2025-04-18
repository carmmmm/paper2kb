import os
import logging
from typing import Optional
from bs4 import BeautifulSoup

from Bio import Entrez
import requests

# ----------------------------------------
# Configuration
# ----------------------------------------

# Use email for NCBI Entrez API (set via .env or fallback)
Entrez.email = os.environ.get("ENTREZ_EMAIL", "example@example.com")

# ----------------------------------------
# Text Retrieval Functions
# ----------------------------------------

def fetch_paper_text(pmid: str, prefer_fulltext: bool = True, return_source: bool = False) -> str | tuple:
    """
    Attempt to fetch the full text of a biomedical paper using a PubMed ID (PMID).

    Tries the following sources in order:
        1. NCBI PMC (PubMed Central) via PMCID
        2. Europe PMC
        3. Entrez abstract fallback

    Args:
        pmid (str): The PubMed ID of the paper.
        prefer_fulltext (bool): Whether to prioritize full text (always True in current usage).
        return_source (bool): If True, return a tuple (text, source) instead of just text.

    Returns:
        str or tuple: Retrieved text (and optionally source).

    Raises:
        RuntimeError: If text retrieval fails from all sources.
    """
    logging.info(f"📥 Attempting full-text retrieval for PMID: {pmid}")

    # -------------------------------
    # Step 1: Try NCBI PMC Full Text
    # -------------------------------
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

    # -------------------------------
    # Step 2: Try Europe PMC Full Text
    # -------------------------------
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

    # -------------------------------
    # Step 3: Fallback to Entrez Abstract
    # -------------------------------
    try:
        handle = Entrez.efetch(db="pubmed", id=pmid, rettype="abstract", retmode="text")
        abstract = handle.read()
        if abstract:
            logging.info("ℹ️ Falling back to abstract via Entrez.")
            return (abstract.strip(), "Entrez abstract") if return_source else abstract.strip()
    except Exception as e:
        logging.warning(f"Entrez fetch failed: {e}")

    # If nothing worked
    raise RuntimeError(f"Unable to retrieve text for PMID {pmid}")

def fetch_local_text(filepath: str) -> Optional[str]:
    """
    Load local text from a file. Used for offline testing or development.

    Args:
        filepath (str): Path to the .txt file.

    Returns:
        str: File contents, stripped of leading/trailing whitespace.

    Raises:
        FileNotFoundError: If the file doesn't exist.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"No such file: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read().strip()