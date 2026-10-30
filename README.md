# HubSpot Data Ingestion Pipeline (Production-Grade ELT)

A robust Data Engineering pipeline that extracts CRM data from the **HubSpot API**, lands compressed **Parquet files in MinIO (S3)**, and incrementally loads and deduplicates data into a **ClickHouse Analytical Warehouse** using `ReplacingMergeTree`.

---

## 📌 Project Architecture

```text
       ┌────────────────────────┐
       │     HubSpot CRM API    │
       └───────────┬────────────┘
                   │
                   ▼  (dlt with incremental cursors: lastmodifieddate / hs_lastmodifieddate)
       ┌────────────────────────┐
       │  Extraction & Ingestion│
       │   (Local Checkpoints)  │
       └───────────┬────────────┘
                   │
                   ▼  (Partitioned Parquet /year=YYYY/month=MM/)
       ┌────────────────────────┐
       │   MinIO Object Storage │  (S3 Data Lake)
       └───────────┬────────────┘
                   │
                   ▼  (Idempotent ClickHouse s3() Engine + ReplacingMergeTree)
       ┌────────────────────────┐
       │  ClickHouse Warehouse  │  (hubspot_dataset)
       │  (Contacts, Companies, │
       │   Deals, Owners, etc.) │
       └───────────┬────────────┘
                   │
                   ▼
       ┌────────────────────────┐
       │    Analytical Views    │  (v_deal_pipeline_summary, v_company_deal_analytics)
       └────────────────────────┘
```

---

## 🛠️ Technology Stack

| Component | Technology | Description |
|---|---|---|
| **Language** | Python 3.10+ | Core pipeline logic & orchestration |
| **Ingestion Engine** | `dlt` (Data Load Tool) | Handles cursor-based incremental sync & schema inference |
| **Data Lake** | MinIO (S3 Compatible) | Stores partitioned, columnar Parquet files |
| **Analytical Warehouse**| ClickHouse | Ultra-fast column-oriented database with `ReplacingMergeTree` |
| **Containerization** | Docker & Docker Compose | Local MinIO & ClickHouse cluster |
| **Deduplication** | ReplacingMergeTree + OPTIMIZE | File-level tracking & record-level deduplication |

---

## 🚀 Key Features Implemented

1. **Incremental Ingestion (`updatedAt` / `lastmodifieddate` cursor):**
   - High-watermark timestamp tracking on contacts (`lastmodifieddate`), companies (`hs_lastmodifieddate`), and deals (`hs_lastmodifieddate`).
   - Prevents redundant full extraction; only new/updated records are pulled.

2. **Persistent Checkpoints & Crash Recovery:**
   - DLT pipeline states are saved in `.dlt/pipelines/hubspot/` to survive crashes and allow pause/resume.

3. **Multi-Table ClickHouse Loader (`load_all_to_clickhouse.py`):**
   - Dynamic schema inference and automated table creation.
   - Idempotent loading via file-tracking table (`hubspot_dataset._loaded_files`).
   - Row-level deduplication via `ReplacingMergeTree(ORDER BY id)` and `OPTIMIZE TABLE ... FINAL`.

4. **Analytical SQL Views (`create_analytical_views.py`):**
   - `hubspot_dataset.v_hubspot_deal_pipeline`: Curated view combining Deals, Companies, and Pipelines for instant business reporting.
   - `hubspot_dataset.v_deal_pipeline_summary`: Aggregates deal volume and pipeline revenue.
   - `hubspot_dataset.v_company_deal_analytics`: Joins company profiles with associated deal values.
   - `hubspot_dataset.v_contact_overview`: Clean view of contacts and recent modifications.

5. **End-to-End Pipeline Automation (`run_pipeline.py`):**
   - Single command execution with structured logging to terminal and `pipeline_execution.log`.

6. **Crash Recovery & Pause/Resume Demo (`demo_crash_and_recovery.py`):**
   - Interactive verification script to simulate worker crash, resume from checkpoint, and verify zero duplicate insertion.

---

## 📂 Project Structure

```text
django-backend-project/
├── .dlt/
│   ├── config.toml               # Destination filesystem & bucket configuration
│   └── secrets.toml              # API keys & MinIO secrets (strictly git-ignored)
├── hubspot/                      # HubSpot dlt source connector & helpers
├── docker-compose.yml            # MinIO & ClickHouse container setup
├── hubspot_pipeline.py           # DLT extraction script with incremental cursors
├── load_all_to_clickhouse.py     # Multi-table ClickHouse loader with deduplication
├── create_analytical_views.py    # ClickHouse analytical SQL views
├── demo_crash_and_recovery.py    # Crash recovery & pause/resume review demo
├── run_pipeline.py               # Master orchestration script
├── requirements.txt              # Project dependencies
├── .env.example                  # Environment template
├── .gitignore                    # Safe git ignore rules
└── README.md                     # Documentation
```

---

## ⚡ Quick Start Guide

### 1. Prerequisites
Ensure Docker Desktop is installed and running on your machine.

### 2. Start Services
```powershell
docker-compose up -d
```
Verify:
- MinIO: `http://localhost:9000` (Console: `http://localhost:9001`)
- ClickHouse HTTP: `http://localhost:8123`

### 3. Setup Virtual Environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 4. Configure Secrets
Ensure `.env` and `.dlt/secrets.toml` contain your HubSpot token and MinIO/ClickHouse credentials.

### 5. Run the End-to-End Pipeline
Execute all stages (Ingestion -> Warehouse Loading -> Views):
```powershell
.\.venv\Scripts\python run_pipeline.py
```

---

## 🔒 Security & Git Hygiene (Task 7 Setup)

Before pushing to GitHub, verify that all sensitive files are excluded:
```powershell
git status
```
Ensure `.env`, `.dlt/secrets.toml`, `.dlt/pipelines/`, and `.venv/` are **not staged**.

```powershell
git add .
git commit -m "feat: complete HubSpot incremental ELT pipeline with MinIO and ClickHouse"
git branch -M main
git remote add origin <YOUR_GITHUB_REPO_URL>
git push -u origin main
```

---

## 👨‍💻 Author
**Arman Ansary** — Data Engineering Project
