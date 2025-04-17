-- schema.sql

DROP TABLE IF EXISTS hgnc_gene;
DROP TABLE IF EXISTS gene_alias;
DROP TABLE IF EXISTS disease;
DROP TABLE IF EXISTS gene_disease;
DROP TABLE IF EXISTS coordinates;

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
                         disease_name TEXT NOT NULL
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
                             hg38_chr TEXT,
                             hg38_start INTEGER,
                             hg38_end INTEGER,
                             hg19_chr TEXT,
                             hg19_start INTEGER,
                             hg19_end INTEGER,
                             FOREIGN KEY (hgnc_id) REFERENCES hgnc_gene(hgnc_id)
);