import sys
import os
import time
from pathlib import Path
import streamlit as st
import pandas as pd
import logging

from src.io_utils import extract_text_from_pdf, load_text_source
from src.fetch_paper import fetch_paper_text
from src.extract_genes import extract_gene_disease_mentions, load_hgnc_reference
from src.get_hgnc_metadata import enrich_with_hgnc
from src.get_coordinates import add_coordinates
from src.normalize_diseases import normalize_diseases
from src.write_output import save_output
from src.db_utils import insert_mentions_to_db

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
logging.basicConfig(level=logging.INFO)

# ---------------- Page Config ----------------
st.set_page_config(page_title="Paper2KB", layout="wide")
st.title("Paper2KB: Paper to KnowledgeBase — Extract Structured Knowledge from Biomedical Papers")

# ---------------- Reset Button ----------------
with st.sidebar:
    if st.button("🔄 RESET for New Paper"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# ---------------- App Info ----------------
with st.expander("ℹ️ About Paper2KB", expanded=False):
    st.markdown("""
    **Paper2KB** extracts gene-disease associations from biomedical texts using hybrid NLP and HGNC data enrichment.  
    You can analyze a paper, customize your export, and download structured JSON/CSV.
    """)

# ---------------- Load HGNC Once ----------------
if "hgnc_loaded" not in st.session_state:
    load_hgnc_reference("data/reference/hgnc_complete_set.txt")
    st.session_state.hgnc_loaded = True

# ---------------- Extraction Settings ----------------
use_hybrid = st.toggle(
    "🧠 Use Hybrid Extraction (NER + HGNC fallback)",
    value=True,
    help="Improves recall by falling back to curated HGNC terms when NER misses gene names."
)

# ---------------- Input Section ----------------
st.subheader("📥 Input a Paper")
input_method = st.radio("Choose Method", ["PMID", "Text Input", "PDF Upload"], horizontal=True)

text = None
source = None
fetch_button = False

if input_method == "PMID":
    pmid = st.text_input("PubMed ID", "38790019")
    fetch_button = st.button("🔍 Fetch & Analyze")
    if fetch_button and pmid:
        with st.spinner("Fetching paper..."):
            text, source = load_text_source(pmid=pmid, localfile=None)

elif input_method == "Text Input":
    text = st.text_area("Paste Abstract or Full Text", height=300)
    fetch_button = st.button("🚀 Analyze Text")
    source = "text input"

elif input_method == "PDF Upload":
    uploaded_pdf = st.file_uploader("Upload PDF", type=["pdf"])
    fetch_button = st.button("📄 Analyze PDF")
    if fetch_button and uploaded_pdf:
        with st.spinner("Extracting text from PDF..."):
            text = extract_text_from_pdf(uploaded_pdf)
            source = "PDF upload"

# ---------------- Inspect SQLite Database ----------------
with st.expander("📂 View SQLite DB contents", expanded=False):
    if st.button("🔎 Show latest HGNC gene + disease links"):
        import sqlite3
        conn = sqlite3.connect("data/outputs/paper2kb.db")
        cur = conn.cursor()
        gene_disease_preview = cur.execute("""
            SELECT g.hgnc_id, g.gene_name, d.disease_name
            FROM hgnc_gene g
            JOIN gene_disease gd ON g.hgnc_id = gd.hgnc_id
            JOIN disease d ON gd.disease_id = d.disease_id
            ORDER BY g.hgnc_id
            LIMIT 50;
        """).fetchall()
        conn.close()
        if gene_disease_preview:
            st.markdown("### 🧬 Gene-Disease Relationships")
            df_preview = pd.DataFrame(gene_disease_preview, columns=["HGNC ID", "Gene", "Disease"])
            st.dataframe(df_preview, use_container_width=True)
        else:
            st.warning("No data found in gene_disease table.")

# ---------------- Processing Pipeline ----------------
if fetch_button and text:
    start = time.time()

    with st.spinner("🔬 Extracting gene and disease mentions..."):
        t0 = time.time()
        mentions, skipped = extract_gene_disease_mentions(text, use_hybrid=use_hybrid, return_skipped=True)
        st.info(f"⏱️ Extraction took {time.time() - t0:.2f}s")

    if not mentions:
        st.warning("No gene-disease mentions found.")
        if skipped:
            st.info(f"{len(skipped)} gene-like terms not matched to HGNC:")
            st.code("\n".join(sorted(set(skipped[:10]))))
        st.stop()

    with st.spinner("🧠 Enriching with HGNC metadata..."):
        t0 = time.time()
        mentions = enrich_with_hgnc(mentions)
        st.info(f"⏱️ HGNC enrichment took {time.time() - t0:.2f}s")

    with st.spinner("🧬 Adding genomic coordinates..."):
        t0 = time.time()
        mentions = add_coordinates(mentions, build="both")
        st.info(f"⏱️ Coordinate lookup took {time.time() - t0:.2f}s")

    with st.spinner("🩺 Normalizing disease mentions..."):
        t0 = time.time()
        mentions = normalize_diseases(mentions)
        st.info(f"⏱️ Disease normalization took {time.time() - t0:.2f}s")

    st.session_state.mentions = mentions
    st.session_state.skipped = skipped
    st.session_state.source = source
    st.session_state.text = text

    st.success(f"✅ Extracted {len(mentions)} mentions (Total runtime: {time.time() - start:.2f}s)")

# ---------------- Display + Export ----------------
if "mentions" in st.session_state:
    mentions = st.session_state.mentions
    skipped = st.session_state.get("skipped", [])
    df = pd.DataFrame(mentions)

    if st.checkbox("📊 Show only table-derived mentions", value=False):
        df = df[df.get("source_section", "body") == "table"]

    if st.checkbox("🔍 Show Source Info", value=True) and "source" in df.columns:
        df["Source"] = df["source"].map({"ner": "🤖 NER", "fallback": "⚡ Fallback"})
        df.insert(0, "Source", df.pop("Source"))

    st.subheader("🧩 Choose Output Columns")
    column_options = [col for col in df.columns if col not in ("source_section",)]
    selected_columns = st.multiselect("Columns to Include", options=column_options, default=column_options)

    st.subheader("📌 Choose Rows")
    selected_indices = st.multiselect("Select rows", options=list(df.index), default=list(df.index))
    filtered_df = df.loc[selected_indices, selected_columns]

    st.dataframe(filtered_df, use_container_width=True)

    st.subheader("💾 Export Results")
    out_format = st.selectbox("Format", ["csv", "json"])
    out_path = f"data/outputs/streamlit_output.{out_format}"
    save_output(filtered_df.to_dict(orient="records"), out_path, fmt=out_format)

    with open(out_path, "rb") as f:
        st.download_button("⬇️ Download File", f, file_name=os.path.basename(out_path))

    if skipped:
        with st.expander(f"⚠️ {len(skipped)} Skipped Genes", expanded=False):
            st.code("\n".join(sorted(set(skipped))))

    # ---------------- Insertion Mode Toggle ----------------
    insertion_mode = st.radio(
        "🧬 Insertion Mode",
        ["Preview Only", "Preview + Save to DB"],
        help="Choose whether to only preview the selected mentions, or also write them to the database."
    )

    # --- Utility: clean semi-colon strings or list into clean list ---
    def split_safe(val):
        if isinstance(val, list):
            return val
        if isinstance(val, str):
            return [s.strip() for s in val.split(";") if s.strip()]
        return []

    def prepare_db_insert_data(df):
        mentions_to_insert = df.to_dict(orient="records")
        cleaned = []
        for item in mentions_to_insert:
            cleaned.append({
                "hgnc_id": item.get("hgnc_id"),
                "name": item.get("name"),
                "diseases": split_safe(item.get("diseases")),
                "alias_symbol": split_safe(item.get("alias_symbol")),
                "hg38_chr": item.get("hg38_chr"),
                "hg38_start": item.get("hg38_start"),
                "hg38_end": item.get("hg38_end"),
                "hg19_chr": item.get("hg19_chr"),
                "hg19_start": item.get("hg19_start"),
                "hg19_end": item.get("hg19_end"),
            })
        return cleaned

    db_ready = prepare_db_insert_data(filtered_df)
    st.markdown("### 🔍 Preview Mentions to be Inserted into Database")
    st.dataframe(pd.DataFrame(db_ready), use_container_width=True)

    if insertion_mode == "Preview + Save to DB":
        if st.button("✅ Save to Database"):
            insert_mentions_to_db(db_ready)
            st.success(f"✅ {len(db_ready)} mentions saved to paper2kb.db!")