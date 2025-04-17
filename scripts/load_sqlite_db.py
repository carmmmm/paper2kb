# scripts/load_sqlite_db.py
import sqlite3
import pandas as pd
from pathlib import Path

def split_safe(val):
    if isinstance(val, list):
        return val
    if isinstance(val, str):
        return [v.strip() for v in val.split(";") if v.strip()]
    return []

# Load cleaned CSV
base = Path(__file__).resolve().parents[1]
csv_path = base / "data" / "outputs" / "streamlit_output.csv"
df = pd.read_csv(csv_path, sep=",", quotechar='"', skipinitialspace=True, on_bad_lines="warn")

# Set up DB
db_path = base / "data" / "outputs" / "paper2kb.db"
db_path.parent.mkdir(parents=True, exist_ok=True)
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Drop tables if they already exist
cur.executescript("""
DROP TABLE IF EXISTS gene_disease;
DROP TABLE IF EXISTS gene_alias;
DROP TABLE IF EXISTS coordinates;
DROP TABLE IF EXISTS disease;
DROP TABLE IF EXISTS hgnc_gene;
""")

# Create schema
cur.executescript("""
CREATE TABLE hgnc_gene (
    hgnc_id TEXT PRIMARY KEY,
    gene_name TEXT NOT NULL
);

CREATE TABLE gene_alias (
    alias_id INTEGER PRIMARY KEY AUTOINCREMENT,
    hgnc_id TEXT NOT NULL,
    alias TEXT NOT NULL,
    FOREIGN KEY (hgnc_id) REFERENCES hgnc_gene(hgnc_id)
);

CREATE TABLE disease (
    disease_id INTEGER PRIMARY KEY AUTOINCREMENT,
    disease_name TEXT NOT NULL UNIQUE
);

CREATE TABLE gene_disease (
    hgnc_id TEXT NOT NULL,
    disease_id INTEGER NOT NULL,
    PRIMARY KEY (hgnc_id, disease_id),
    FOREIGN KEY (hgnc_id) REFERENCES hgnc_gene(hgnc_id),
    FOREIGN KEY (disease_id) REFERENCES disease(disease_id)
);

CREATE TABLE coordinates (
    hgnc_id TEXT PRIMARY KEY,
    hg38_chr TEXT, hg38_start INTEGER, hg38_end INTEGER,
    hg19_chr TEXT, hg19_start INTEGER, hg19_end INTEGER,
    FOREIGN KEY (hgnc_id) REFERENCES hgnc_gene(hgnc_id)
);
""")

# Insert hgnc_gene and coordinates
for _, row in df.iterrows():
    cur.execute("INSERT OR IGNORE INTO hgnc_gene (hgnc_id, gene_name) VALUES (?, ?)",
                (row["hgnc_id"], row["name"]))
    cur.execute("INSERT OR REPLACE INTO coordinates VALUES (?, ?, ?, ?, ?, ?, ?)", (
        row["hgnc_id"], row["hg38_chr"], row["hg38_start"], row["hg38_end"],
        row["hg19_chr"], row["hg19_start"], row["hg19_end"]
    ))

# Insert aliases
for _, row in df.iterrows():
    for alias in split_safe(row.get("alias_symbol", "")):
        cur.execute("INSERT INTO gene_alias (hgnc_id, alias) VALUES (?, ?)", (row["hgnc_id"], alias))

# Insert diseases
for _, row in df.iterrows():
    for disease in split_safe(row.get("diseases", "")):
        cur.execute("INSERT OR IGNORE INTO disease (disease_name) VALUES (?)", (disease,))
        cur.execute("SELECT disease_id FROM disease WHERE disease_name = ?", (disease,))
        disease_id = cur.fetchone()[0]
        cur.execute("INSERT OR IGNORE INTO gene_disease (hgnc_id, disease_id) VALUES (?, ?)",
                    (row["hgnc_id"], disease_id))

conn.commit()
conn.close()
print(f"✅ SQLite DB created at {db_path}")