import logging
import os
import fitz

from paper2kb.fetch_paper import fetch_paper_text

def extract_text_from_pdf(uploaded_file):
    with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
        return "\n".join([page.get_text() for page in doc])

def load_text_source(pmid=None, localfile=None):
    if localfile:
        logging.info(f"Reading from local file: {localfile}")
        if localfile.endswith(".pdf"):
            text = extract_text_from_pdf(localfile)
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
            logging.error(f"Failed to fetch paper text: {e}")
            raise
    else:
        raise ValueError("Must provide either PMID or local file path.")

def infer_output_path(pmid=None, localfile=None, format="json", outdir="data/outputs"):
    os.makedirs(outdir, exist_ok=True)
    if pmid:
        basename = f"pmid{pmid}"
    elif localfile:
        stem = os.path.splitext(os.path.basename(localfile))[0]
        basename = f"{stem}_parsed"
    else:
        raise ValueError("Cannot infer output path without PMID or localfile")
    return os.path.join(outdir, f"{basename}.{format}")