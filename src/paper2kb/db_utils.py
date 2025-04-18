import sqlite3
from pathlib import Path

# Path to the SQLite database
DB_PATH = Path("data/outputs/paper2kb.db")

def insert_mentions_to_db(mentions):
    """
    Insert a list of gene-disease mention dictionaries into the SQLite database.

    Each mention should include:
        - hgnc_id: HGNC identifier for the gene
        - name: official gene name
        - alias_symbol: list of aliases for the gene
        - diseases: list of associated disease names
        - hg38/hg19 coordinates: genomic location information

    Handles deduplication using INSERT OR IGNORE/REPLACE logic.
    Logs potential name mismatches or missing data.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    duplicates = []  # Tracks conflicting gene name entries for the same HGNC ID
    skipped = []     # Tracks entries missing a valid gene name

    for item in mentions:
        hgnc_id = item.get("hgnc_id")
        name = item.get("name")

        # Skip entries missing a name or with invalid types
        if not name or isinstance(name, (int, float)):
            skipped.append((hgnc_id, name))
            continue

        # Insert gene into hgnc_gene table, ignoring duplicates
        cur.execute("INSERT OR IGNORE INTO hgnc_gene (hgnc_id, gene_name) VALUES (?, ?)", (hgnc_id, name))

        # Check for existing entries with different names (log but don't overwrite)
        cur.execute("SELECT gene_name FROM hgnc_gene WHERE hgnc_id = ?", (hgnc_id,))
        existing_name = cur.fetchone()
        if existing_name and existing_name[0] != name:
            duplicates.append((hgnc_id, existing_name[0], name))

        # Insert gene aliases
        for alias in item.get("alias_symbol", []):
            cur.execute("INSERT OR IGNORE INTO gene_alias (hgnc_id, alias) VALUES (?, ?)", (hgnc_id, alias))

        # Insert diseases and link them to the gene
        for disease in item.get("diseases", []):
            if not disease:
                continue
            cur.execute("INSERT OR IGNORE INTO disease (disease_name) VALUES (?)", (disease,))
            cur.execute("SELECT disease_id FROM disease WHERE disease_name = ?", (disease,))
            disease_result = cur.fetchone()
            if disease_result:
                disease_id = disease_result[0]
                cur.execute("INSERT OR IGNORE INTO gene_disease (hgnc_id, disease_id) VALUES (?, ?)", (hgnc_id, disease_id))

        # Insert or update coordinate information
        cur.execute("""
            INSERT OR REPLACE INTO coordinates (
                hgnc_id, hg38_chr, hg38_start, hg38_end,
                hg19_chr, hg19_start, hg19_end
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            hgnc_id,
            item.get("hg38_chr"), item.get("hg38_start"), item.get("hg38_end"),
            item.get("hg19_chr"), item.get("hg19_start"), item.get("hg19_end")
        ))

    # Commit and close the database connection
    conn.commit()
    conn.close()

    # Report potential name conflicts
    if duplicates:
        print("⚠️ Potential gene ID conflicts found:")
        for hgnc_id, existing, new in duplicates:
            print(f" - {hgnc_id}: '{existing}' (existing) vs '{new}' (new)")

    # Report skipped entries
    if skipped:
        print("⚠️ Skipped genes with missing or invalid names:")
        for hgnc_id, name in skipped:
            print(f" - {hgnc_id}: name = {name}")