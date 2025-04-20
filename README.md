# 📘 Paper2KB: Biomedical Knowledgebase Extractor

![Python](https://img.shields.io/badge/python-3.10+-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Tests](https://img.shields.io/badge/tests-passing-brightgreen)

Paper2KB is a modular, end-to-end pipeline that ingests biomedical literature—from PubMed 
abstracts to full-text PDFs—and extracts gene-disease relationships using named entity 
recognition and HGNC-backed matching. It enriches results with official gene metadata, 
genomic coordinates, and MONDO-normalized disease concepts, producing clean, structured 
outputs ready for downstream analysis, database integration, and clinical curation workflows.

<img width="956" alt="Screenshot 2025-04-18 at 12 19 08 AM" src="https://github.com/user-attachments/assets/3c08542e-e51a-498b-877e-e5a4a1d59ffd" />


---

## 🚀 What It Does

### 💾 Fetch Paper Text
- Accepts **PMID**, raw text, or **PDF**
- Retrieves full text using **NCBI Entrez** or **Europe PMC**

### 🧬 Gene-Disease Extraction
- Named Entity Recognition (SciSpacy models)
- HGNC fallback matching to maximize recall
- Extracts gene–disease pairs with sentence-level context

### 🧠 Metadata Enrichment
- HGNC name, ID, aliases
- Genome coordinates (hg19 + hg38 via Ensembl REST)
- Disease normalization to MONDO

### 📤 Export + Review
- Choose specific columns and rows to export 
- Save output as JSON or CSV with flattened, human-readable formatting 
- View and interactively explore data in a Streamlit interface
  <img width="647" alt="Screenshot 2025-04-18 at 12 18 45 AM" src="https://github.com/user-attachments/assets/744370f0-5dec-4d0c-bae2-bdf82331672a" />


### 🧱 SQLite Knowledgebase
- Insert extracted mentions into a mock relational SQLite database 
  - Tables: `hgnc_gene`, `gene_alias`, `disease`, `gene_disease`, `coordinates`
- Supports deduplication, alias tracking, and normalized relationships 
- View current DB state directly from the UI or via SQL queries 
- Includes prebuilt schema and example queries for integration into real pipelines
- Schema and ER diagram included

### 🧭 Access Methods
- Command-Line Interface (CLI)
  - Fetch + parse papers by PMID, PDF, or Text
  - Output to JSON/CSV
- Streamlit Web App
  - Full UI for input + preview
  - Select rows/columns to save
  - Insert into SQLite DB
  - View database contents live
 
<img width="979" alt="Screenshot 2025-04-18 at 1 39 10 AM" src="https://github.com/user-attachments/assets/839428ef-6512-45d7-8349-779f493fd35d" />


---

## 🏃 Getting Started 

### 📁 Directory Structure

```bash
paper2kb/
├── data/
│   ├── outputs/                  # Extracted outputs and generated database
│   │   └── example_output.csv
│   └── reference/                # HGNC reference files
├── scripts/
│   ├── outputs/                  # DB generator output
│   │   └── paper2kb.db
│   ├── load_sqlite_db.py         # Script to load output into SQLite
│   ├── run_pipeline.sh           # Optional shell runner
│   └── update_hgnc.py            # Fetch latest HGNC data
├── sql/
│   ├── schema.sql                # SQLite schema definition
│   ├── sample_queries.sql        # SQL examples for querying data
│   └── schema_diagram.png        # Entity-relationship diagram
├── src/
│   └── paper2kb/
│       ├── __init__.py
│       ├── cli.py                # CLI entry point
│       ├── db_utils.py           # SQLite insert logic
│       ├── extract_genes.py      # NER + fallback extraction
│       ├── fetch_paper.py        # Text retrieval (PMID/PDF/Raw)
│       ├── get_coordinates.py    # Ensembl + liftover genomic coords
│       ├── get_hgnc_metadata.py  # HGNC metadata enrichment
│       ├── io_utils.py           # Text loading + inference
│       ├── normalize_diseases.py # MONDO term mapping
│       ├── opentargets_utils.py  # Fallback gene-disease links
│       └── write_output.py       # JSON/CSV writer
├── streamlit_app/
│   └── app.py                    # Interactive UI
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_end_to_end.py
│   ├── test_extract_genes.py
│   ├── test_fetch_paper.py
│   ├── test_get_coordinates.py
│   ├── test_get_metadata.py
│   ├── test_normalize_diseases.py
│   ├── test_write_output.py
│   └── tests_cli.py
├── .env.example                 # Sample environment config
├── environment.yml             # Conda environment (if applicable)
├── requirements.txt            # pip install dependencies
├── setup.py                    # pip-installable package config
├── pyproject.toml              # Project metadata and build system
└── README.md                   # Overview and usage guide
```

### First Steps
 1. First, clone Paper2KB to your local machine. Make sure you have Python 3.10 installed.

        ```
        git clone https://github.com/yourusername/paper2kb.git
        cd paper2kb
        ```
 2. Environment Setup

    OPTION 1: With pip + virtualenv

    ```
    python3.10 -m venv .venv310
    source .venv310/bin/activate
    pip install -r requirements.txt
    ```
    
    OPTION 2: With Conda

    ```
    conda env create -f environment.yml
    conda activate paper2kb
    ```
    
 3. To use NCBI Entrez API, create a .env file in the project root:

    ```
    cp .env.example .env
    ```
    
    Then edit it with your email.

    ```
    nano .env
    ENTREZ_EMAIL=your@email.com
    ```
  
 4. Populate the SQLite Database (Optional but Recommended)
    To initialize the database with example data from example_output.csv, run:
    ```
    python scripts/load_sqlite_db.py
    ```

    You’ll see a confirmation like:
    
    ```
    ✅ SQLite DB created at /absolute/path/to/paper2kb/data/outputs/paper2kb.db
    ```


Now you must decide whether you want to access via the StreamLit App or the CLI.

| Access Method     | Purpose                                      | UI/UX        | Best For                      |
|-------------------|----------------------------------------------|--------------|-------------------------------|
| **Streamlit App** | Full-featured interactive interface          | Graphical UI | Exploratory use, customization |
| **CLI Tool**      | Fast extraction pipeline with minimal setup  | Command-line | Automation, scripting         |

### 🌟From the StreamLit App 
1. Start the App

    ```
   streamlit run streamlit_app/app.py
   ```
   
2. Choose input 
   - PubMed ID (e.g. 38790019)
   - Paste in text 
   - Upload a PDF

3. Customize your output 
   - Select rows + columns
<img width="647" alt="Screenshot 2025-04-18 at 12 18 45 AM" src="https://github.com/user-attachments/assets/ecbf43aa-11f5-49e6-a50d-df14fe2c1b19" />


   - Export to CSV/JSON
<img width="972" alt="Screenshot 2025-04-18 at 1 38 41 AM" src="https://github.com/user-attachments/assets/b049575d-eacc-45ec-98be-6902e8b72cf9" />


   - Optionally insert into SQLite DB
<img width="979" alt="Screenshot 2025-04-18 at 1 43 24 AM" src="https://github.com/user-attachments/assets/c90c84e9-6c2d-4d85-8047-82db0ef59af1" />


5. Database Preview 
   - View DB contents via sidebar 
   - Confirm gene/disease links visually

<img width="977" alt="Screenshot 2025-04-18 at 1 43 53 AM" src="https://github.com/user-attachments/assets/37ca3c71-4a7b-4493-a9ce-096038d73dd9" />


### 💻 From the CLI

Run a complete extraction pipeline directly from the terminal:

```
paper2kb --pmid 38790019 --format csv
```

Or use a local file:

```
paper2kb --localfile path/to/paper.pdf --format json
```

Other CLI flags:

- `--mode hybrid` (default) or `--mode ml`
- `--build hg19`, `hg38`, or `both`
- `--output path/to/file.csv`
- `--debug` for verbose logs

Output will be saved to `data/outputs/`, along with a list of skipped genes.

---

## 🧱 Understanding the Database Structure

Paper2KB includes a **relational SQLite database** (`paper2kb.db`) that organizes all extracted information into normalized tables. This design supports easy joins, deduplication, and scalable querying.

The schema consists of:

- `hgnc_gene`: Stores the official HGNC ID and gene name
- `gene_alias`: Captures known aliases for each gene
- `disease`: Lists all unique disease mentions (normalized or raw)
- `gene_disease`: Many-to-many mapping between genes and diseases
- `coordinates`: Stores HG19 and HG38 genomic coordinates for each gene

The schema diagram is included in [`sql/schema_diagram.png`](sql/schema_diagram.png), and all definitions are written out in [`sql/schema.sql`](sql/schema.sql).

---

### ✅ Example Queries

```sql
-- 1. HGNC ID and disease connection
SELECT g.hgnc_id, d.disease_name
FROM hgnc_gene g
         JOIN gene_disease gd ON g.hgnc_id = gd.hgnc_id
         JOIN disease d ON gd.disease_id = d.disease_id;

-- Example Results 
hgnc_id     disease_name                      
----------  ----------------------------------
HGNC:3942   tubulopathy                       
HGNC:3942   dilated cardiomyopathy            
HGNC:11621  mody                              
HGNC:618    kidney disease                    
HGNC:618    proteinuria                       
HGNC:618    focal segmental glomerulosclerosis
HGNC:618    sepsis                            
HGNC:13394  kidney disease                    
HGNC:13394  nephrotic syndrome                
HGNC:13394  proteinuria                       
HGNC:13394  focal segmental glomerulosclerosis
HGNC:13394  hypertension                      
HGNC:2204   hypertension                      
HGNC:2204   alport syndrome          

-- 2. HGNC Gene Name and aliases
SELECT g.gene_name, GROUP_CONCAT(a.alias, ', ') AS aliases
FROM hgnc_gene g
         LEFT JOIN gene_alias a ON g.hgnc_id = a.hgnc_id
GROUP BY g.gene_name;

-- Example Results 
gene_name                                                     aliases                                               
------------------------------------------------------------  ------------------------------------------------------
HECT and RLD domain containing E3 ubiquitin protein ligase 2  D15F37S1, D15F37S1, jdf2, jdf2, p528, p528            
HNF1 homeobox A                                               HNF1, HNF1, HNF1α, HNF1α, LFB1, LFB1                  
NPHS2 stomatin family member, podocin                         PDCN, PDCN, SRN1, SRN1                                
Ras related GTP binding D                                     DKFZP761H171, DKFZP761H171, bA11D8.2.1, bA11D8.2.1    
apolipoprotein L1                                                                                                   
collagen type IV alpha 3 chain                                                                                      
matrix Gla protein                                                                                                  
mechanistic target of rapamycin kinase                        FLJ44809, FLJ44809, RAFT1, RAFT1, RAPT1, RAPT1        
structural maintenance of chromosomes 3                       BAM, BAM, HCAP, HCAP, SMC3L1, SMC3L1, bamacan, bamacan

```

---

## 🧪 Testing

Includes:
- Functional unit tests for each module
- End-to-end test: NER → enrichment → coordinate mapping → MONDO normalization
- CLI test coverage via `subprocess`

Run unit tests and CLI tests with:

```bash
pytest -v
```

---

## 👩‍💻 Author

**Carmen Montero**  
Clinical Technology + Software Engineer

---

## 📜 License

MIT License
