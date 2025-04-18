import sys
from pathlib import Path

# Add project root to sys.path so internal modules work when run as CLI
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import argparse
import logging
import os
import time
from dotenv import load_dotenv

from Bio import Entrez
from paper2kb.extract_genes import extract_gene_disease_mentions, load_hgnc_reference
from paper2kb.get_hgnc_metadata import enrich_with_hgnc
from paper2kb.get_coordinates import add_coordinates
from paper2kb.normalize_diseases import normalize_diseases
from paper2kb.write_output import save_output
from paper2kb.io_utils import load_text_source, infer_output_path

# Load environment variables (for NCBI Entrez API access)
load_dotenv()
Entrez.email = os.environ.get("ENTREZ_EMAIL", "fallback@example.com")

# Set up logging format and default level
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

def main():
    """
    Command-line entry point for Paper2KB.

    Supports fetching paper text (by PMID or file), extracting gene–disease pairs,
    enriching them with HGNC metadata and genomic coordinates, normalizing disease names,
    and exporting results as structured CSV/JSON.
    """

    # Argument parser setup
    parser = argparse.ArgumentParser(description="Parse gene-disease metadata from a scientific paper.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--pmid', type=str, help='PubMed ID of the publication')
    group.add_argument('--localfile', type=str, help='Path to a local .txt or .pdf file')

    parser.add_argument('--build', choices=['hg19', 'hg38', 'both'], default='both', help='Genome build')
    parser.add_argument('--format', choices=['json', 'csv'], default='json', help='Output format')
    parser.add_argument('--output', type=str, help='Output file path (optional — auto inferred if not provided)')
    parser.add_argument('--mode', choices=['ml', 'hybrid'], default='hybrid',
                        help='Extraction mode: ml (NER only) or hybrid (NER + HGNC fallback)')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')

    args = parser.parse_args()
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    start_total = time.time()

    # Load HGNC reference for matching + enrichment
    logging.info("📥 Loading HGNC reference...")
    load_hgnc_reference("data/reference/hgnc_complete_set.txt")

    # Load full text using chosen input method
    logging.info("📄 Will try full text via Europe PMC, fallback to abstract if unavailable.")
    logging.info("📄 Retrieving paper text...")
    text, source = load_text_source(pmid=args.pmid, localfile=args.localfile)
    logging.info(f"🧾 Text source: {source}")

    # Determine where to save output
    if not args.output:
        args.output = infer_output_path(pmid=args.pmid, localfile=args.localfile, format=args.format)
        logging.info(f"💾 Inferred output path: {args.output}")

    # Extract gene–disease pairs
    logging.info(f"🔍 Extracting gene-disease mentions with mode: {args.mode}")
    t0 = time.time()
    use_hybrid = args.mode == "hybrid"
    gene_pairs, skipped = extract_gene_disease_mentions(text, use_hybrid=use_hybrid, return_skipped=True)
    logging.info(f"⏱️ Gene/Disease extraction completed in {time.time() - t0:.2f}s")

    logging.info(f"🧬 Found {len(gene_pairs)} matched gene(s)")

    # Save skipped gene terms, if any
    if skipped:
        skipped_path = args.output.replace(".json", "_skipped.txt").replace(".csv", "_skipped.txt")
        with open(skipped_path, "w") as f:
            f.write("\n".join(sorted(set(skipped))))
        logging.info(f"📄 Saved unrecognized genes to: {skipped_path}")

    if not gene_pairs:
        logging.error("❌ No gene-disease mentions found — exiting.")
        return

    # Enrich gene data with official HGNC metadata
    logging.info("🧠 Enriching with HGNC metadata...")
    t0 = time.time()
    enriched = enrich_with_hgnc(gene_pairs)
    logging.info(f"⏱️ HGNC enrichment completed in {time.time() - t0:.2f}s")

    # Add genomic coordinates from Ensembl REST API
    logging.info(f"🧬 Adding genomic coordinates ({args.build})...")
    t0 = time.time()
    with_coords = add_coordinates(enriched, build=args.build)
    logging.info(f"⏱️ Coordinate lookup completed in {time.time() - t0:.2f}s")

    # Normalize diseases to MONDO concepts
    logging.info("🩺 Normalizing disease mentions...")
    t0 = time.time()
    final = normalize_diseases(with_coords)
    logging.info(f"⏱️ Disease normalization completed in {time.time() - t0:.2f}s")

    # Preview a sample of the output
    logging.info("🪪 Final result preview (first 3 rows):")
    for item in final[:3]:
        logging.info(item)

    # Save result to CSV or JSON
    logging.info(f"📤 Writing output to {args.output}")
    save_output(final, args.output, fmt=args.format)
    logging.info(f"🎉 Done! Total runtime: {time.time() - start_total:.2f}s")


if __name__ == "__main__":
    main()