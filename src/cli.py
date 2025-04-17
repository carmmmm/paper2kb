import argparse
import logging
import os
import time
from dotenv import load_dotenv

from Bio import Entrez
from extract_genes import extract_gene_disease_mentions, load_hgnc_reference
from get_hgnc_metadata import enrich_with_hgnc
from get_coordinates import add_coordinates
from normalize_diseases import normalize_diseases
from write_output import save_output
from io_utils import load_text_source, infer_output_path
from opentargets_utils import get_opentargets_diseases

load_dotenv()
Entrez.email = os.environ.get("ENTREZ_EMAIL", "fallback@example.com")

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

def main():
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

    logging.info("📥 Loading HGNC reference...")
    load_hgnc_reference("data/reference/hgnc_complete_set.txt")

    logging.info("📄 Will try full text via Europe PMC, fallback to abstract if unavailable.")
    logging.info("📄 Retrieving paper text...")
    text, source = load_text_source(pmid=args.pmid, localfile=args.localfile)
    logging.info(f"🧾 Text source: {source}")

    if not args.output:
        args.output = infer_output_path(pmid=args.pmid, localfile=args.localfile, format=args.format)
        logging.info(f"💾 Inferred output path: {args.output}")

    logging.info(f"🔍 Extracting gene-disease mentions with mode: {args.mode}")
    t0 = time.time()
    use_hybrid = args.mode == "hybrid"
    gene_pairs, skipped = extract_gene_disease_mentions(text, use_hybrid=use_hybrid, return_skipped=True)
    logging.info(f"⏱️ Gene/Disease extraction completed in {time.time() - t0:.2f}s")

    logging.info(f"🧬 Found {len(gene_pairs)} matched gene(s)")
    if skipped:
        skipped_path = args.output.replace(".json", "_skipped.txt").replace(".csv", "_skipped.txt")
        with open(skipped_path, "w") as f:
            f.write("\n".join(sorted(set(skipped))))
        logging.info(f"📄 Saved unrecognized genes to: {skipped_path}")

    if not gene_pairs:
        logging.error("❌ No gene-disease mentions found — exiting.")
        return

    logging.info("🧠 Enriching with HGNC metadata...")
    t0 = time.time()
    enriched = enrich_with_hgnc(gene_pairs)
    logging.info(f"⏱️ HGNC enrichment completed in {time.time() - t0:.2f}s")

    logging.info(f"🧬 Adding genomic coordinates ({args.build})...")
    t0 = time.time()
    with_coords = add_coordinates(enriched, build=args.build)
    logging.info(f"⏱️ Coordinate lookup completed in {time.time() - t0:.2f}s")

    logging.info("🩺 Normalizing disease mentions...")
    t0 = time.time()
    final = normalize_diseases(with_coords)
    logging.info(f"⏱️ Disease normalization completed in {time.time() - t0:.2f}s")

    logging.info("🪪 Final result preview (first 3 rows):")
    for item in final[:3]:
        logging.info(item)

    logging.info(f"📤 Writing output to {args.output}")
    save_output(final, args.output, fmt=args.format)
    logging.info(f"🎉 Done! Total runtime: {time.time() - start_total:.2f}s")

if __name__ == "__main__":
    main()
