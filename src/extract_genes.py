import spacy
from opentargets_utils import get_opentargets_diseases
from pathlib import Path
import csv
import logging
import re
import json

HGNC_SYMBOLS = set()
HGNC_ALIASES = {}
GENE_DISEASE_MAP = {}  # gene symbol → set of disease strings
COMMON_WORD_GENES = {
    "SET", "SHE", "WAS", "HAS", "AND", "ARE", "ONE", "ANY", "ALL", "ASK",
    "ACT", "CAN", "MAP", "BAM", "BAD", "ITS", "MAN", "MAY", "NOT", "OUT",
    "RUN", "TIP", "TOP", "YET", "TRY", "USE", "YES", "NOW", "NEW", "LET",
    "NET", "GAP", "GAS", "HIT", "TAG", "ZIP", "POP", "BIT", "BAT", "WIN",
    "LOW", "UP", "ON", "OFF", "IN", "IT", "TO", "DO", "BY", "NO", "BE",
    "GO", "SO", "OF", "AT", "IF", "AS", "WE", "HE", "OR", "MY", "ME",
    "MGP", "BAM", "SET", "SHE", "WAS", "AR", "AND", "MAN", "MAP"
}  # genes prone to false positives

def load_hgnc_reference(filepath: str):
    """Load HGNC gene symbols and aliases from local TSV file."""
    global HGNC_SYMBOLS, HGNC_ALIASES
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            symbol = row["symbol"].upper()
            HGNC_SYMBOLS.add(symbol)
            if row["alias_symbol"]:
                for alias in row["alias_symbol"].split("|"):
                    alias = alias.upper()
                    HGNC_ALIASES[alias] = symbol

# Load NER models
GENE_NLP = spacy.load("en_ner_jnlpba_md")     # Genes
DISEASE_NLP = spacy.load("en_ner_bc5cdr_md")  # Diseases

def extract_gene_disease_mentions(text: str, use_hybrid: bool = True, return_skipped: bool = False) -> list[dict]:
    gene_doc = GENE_NLP(text)
    disease_doc = DISEASE_NLP(text)

    results = []
    skipped_genes = []
    seen_mentions = set()

    # Build disease map and all unique disease mentions
    disease_by_sent = {}
    disease_mentions = set()
    for ent in disease_doc.ents:
        if ent.label_ == "DISEASE":
            sentence = ent.sent.text.strip()
            disease_by_sent.setdefault(sentence, []).append(ent.text)
            disease_mentions.add(ent.text.lower())

    # STEP 1: ML-based gene extraction
    for sent in gene_doc.sents:
        sentence_text = sent.text.strip()
        gene_mentions = [
            ent.text.upper()
            for ent in sent.ents
            if ent.label_ in {"DNA", "RNA", "PROTEIN"}
        ]

        for gene in gene_mentions:
            if gene in HGNC_SYMBOLS:
                normalized = gene
            elif gene in HGNC_ALIASES:
                normalized = HGNC_ALIASES[gene]
            else:
                skipped_genes.append(gene)
                continue

            if normalized in seen_mentions:
                continue
            seen_mentions.add(normalized)

            results.append({
                "symbol": normalized,
                "original_mention": gene,
                "sentence": sentence_text,
                "diseases": disease_by_sent.get(sentence_text, []),
                "source": "ner",
                "source_section": "table" if "table" in sentence_text.lower() else "body"
            })

    # STEP 2: Optional hybrid fallback (regex-style HGNC matching)
    if use_hybrid:
        for hgnc_symbol in HGNC_SYMBOLS:
            if hgnc_symbol in seen_mentions:
                continue

            if hgnc_symbol in COMMON_WORD_GENES:
                # only allow fallback if it's fully capitalized and appears with context
                if not re.search(rf"\\b{hgnc_symbol}\\b", text):
                    continue

            pattern = r'\b' + re.escape(hgnc_symbol) + r'\b'
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                span = match.start()
                snippet = text[max(0, span - 100): span + 100]
                inferred_sentence = snippet.strip().replace("\n", " ")

                # Live DisGeNET lookup!
                known_diseases = set(get_opentargets_diseases(hgnc_symbol))
                matched_diseases = [d for d in disease_mentions if d in known_diseases]

                results.append({
                    "symbol": hgnc_symbol,
                    "original_mention": hgnc_symbol,
                    "sentence": inferred_sentence,
                    "diseases": matched_diseases,
                    "source": "fallback",
                    "source_section": "table" if "table" in inferred_sentence.lower() else "body"
                })
                seen_mentions.add(hgnc_symbol)
                logging.debug(f"⚡ Fallback match: {hgnc_symbol}")

    # STEP 3: Logging
    if skipped_genes:
        preview = ", ".join(sorted(set(skipped_genes))[:10])
        logging.warning(f"⚠️ Skipped {len(skipped_genes)} unrecognized gene(s). First few: {preview}")

    return results if not return_skipped else (results, skipped_genes)
