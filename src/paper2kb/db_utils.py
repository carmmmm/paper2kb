import sqlite3
from pathlib import Path

DB_PATH = Path("data/outputs/paper2kb.db")

def insert_mentions_to_db(mentions):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    duplicates = []
    skipped = []

    for item in mentions:
        hgnc_id = item.get("hgnc_id")
        name = item.get("name")

        # Skip if name is missing or suspicious
        if not name or isinstance(name, (int, float)):
            skipped.append((hgnc_id, name))
            continue

        cur.execute("INSERT OR IGNORE INTO hgnc_gene (hgnc_id, gene_name) VALUES (?, ?)", (hgnc_id, name))

        # Log if this hgnc_id already exists with a different name
        cur.execute("SELECT gene_name FROM hgnc_gene WHERE hgnc_id = ?", (hgnc_id,))
        existing_name = cur.fetchone()
        if existing_name and existing_name[0] != name:
            duplicates.append((hgnc_id, existing_name[0], name))

        for alias in item.get("alias_symbol", []):
            cur.execute("INSERT OR IGNORE INTO gene_alias (hgnc_id, alias) VALUES (?, ?)", (hgnc_id, alias))

        for disease in item.get("diseases", []):
            if not disease:
                continue
            cur.execute("INSERT OR IGNORE INTO disease (disease_name) VALUES (?)", (disease,))
            cur.execute("SELECT disease_id FROM disease WHERE disease_name = ?", (disease,))
            disease_result = cur.fetchone()
            if disease_result:
                disease_id = disease_result[0]
                cur.execute("INSERT OR IGNORE INTO gene_disease (hgnc_id, disease_id) VALUES (?, ?)", (hgnc_id, disease_id))

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

    conn.commit()
    conn.close()

    if duplicates:
        print("⚠️ Potential gene ID conflicts found:")
        for d in duplicates:
            print(f" - {d[0]}: '{d[1]}' (existing) vs '{d[2]}' (new)")

    if skipped:
        print("⚠️ Skipped genes with missing or invalid names:")
        for s in skipped:
            print(f" - {s[0]}: name = {s[1]}")