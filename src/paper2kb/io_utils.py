import logging
import os
import fitz  # PyMuPDF
from paper2kb.fetch_paper import fetch_paper_text

def extract_text_from_pdf(uploaded_file):
    """
    Extracts text from a PDF file-like object using PyMuPDF.

    Args:
        uploaded_file: File-like object (e.g., from Streamlit or file upload).

    Returns:
        str: Extracted text from all pages.
    """
    with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
        return "\n".join(page.get_text() for page in doc)


def load_text_source(pmid=None, localfile=None):
    """
    Load the text content of a biomedical paper.

    Prioritizes local files (PDF or TXT), or falls back to fetching from PubMed via PMID.

    Args:
        pmid (str, optional): PubMed ID of the paper.
        localfile (str, optional): Path to a local text or PDF file.

    Returns:
        tuple: (paper_text, source_description)

    Raises:
        ValueError: If neither `pmid` nor `localfile` is provided.
        Exception: If fetching from PubMed fails.
    """
    if localfile:
        logging.info(f"Reading from local file: {localfile}")
        if localfile.endswith(".pdf"):
            with open(localfile, "rb") as f:
                text = extract_text_from_pdf(f)
        else:
            with open(localfile, "r", encoding="utf-8") as f:
                text = f.read()
        if not text.strip():
            logging.warning("Local file appears to be empty. Are you sure it's plain text or a readable PDF?")
        return text, "localfile"

    elif pmid:
        try:
            text, source = fetch_paper_text(pmid, return_source=True)
            return text, source
        except Exception as e:
            logging.error(f"Failed to fetch paper text for PMID {pmid}: {e}")
            raise

    else:
        raise ValueError("Must provide either `pmid` or `localfile`.")


def infer_output_path(pmid=None, localfile=None, format="json", outdir="data/outputs"):
    """
    Infer a reasonable output file path based on input source.

    Args:
        pmid (str, optional): PubMed ID.
        localfile (str, optional): Local file path.
        format (str): 'json' or 'csv'
        outdir (str): Output directory path.

    Returns:
        str: Full file path for output file.
    """
    os.makedirs(outdir, exist_ok=True)

    if pmid:
        basename = f"pmid{pmid}"
    elif localfile:
        stem = os.path.splitext(os.path.basename(localfile))[0]
        basename = f"{stem}_parsed"
    else:
        raise ValueError("Cannot infer output path without PMID or localfile.")

    return os.path.join(outdir, f"{basename}.{format}")