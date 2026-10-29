# django-backend-project
Django Backend Internship Assignment
# HubSpot Data Ingestion Pipeline

A data engineering project to extract CRM data from HubSpot, store compressed Parquet files in MinIO, and load the data into ClickHouse for analytics.

## 📌 Project Overview

The goal of this project is to build a reliable and scalable data ingestion pipeline using Python and `dlt` (Data Load Tool).

The pipeline will support incremental data ingestion, persistent checkpoints, parallel processing, and crash recovery to minimize duplicate records and prevent data loss.

## 🎯 Objectives

- Extract CRM data from the HubSpot API.
- Use `dlt` to manage data extraction and pipeline state.
- Store compressed Parquet files in MinIO object storage.
- Load ingested data into ClickHouse for analytical queries.
- Implement incremental ingestion using updated-at timestamps.
- Support pause and resume functionality.
- Recover safely from unexpected process termination.
- Support parallel ingestion of multiple resources.
- Build analytical views joining Deals, Companies, and Pipelines.

## 🛠️ Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| Data Ingestion | dlt |
| Source API | HubSpot CRM API |
| Data Format | Parquet |
| Object Storage | MinIO |
| Analytics Database | ClickHouse |
| Containerization | Docker |
| Configuration | Python dotenv, TOML |

## 🏗️ Architecture

```text
HubSpot CRM API
       |
       v
 Python + dlt
       |
       v
 Data Extraction
       |
       v
 Incremental Processing
       |
       v
 Compressed Parquet Files
       |
       v
 MinIO Object Storage
       |
       v
 ClickHouse
       |
       v
 Analytical Views & Queries
```

## 📦 Planned Data Resources

The pipeline is intended to ingest the following HubSpot resources:

- Contacts
- Companies
- Deals
- Tickets
- Line Items
- Engagements
- Pipelines
- Owners

**Note:** Resource support will be verified and implemented as development progresses.

## ⚙️ Prerequisites

Install the following before running the project:

- Python 3.10 or a compatible version supported by the installed dependencies
- Docker Desktop
- Git
- A HubSpot account with the required API permissions
- Visual Studio Code (recommended)

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd hubspot-ingestion
```

Replace the repository URL with your actual GitHub repository URL.

### 2. Create a virtual environment

```powershell
python -m venv .venv
```

Activate it in Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```dotenv
HUBSPOT_ACCESS_TOKEN=YOUR_HUBSPOT_SERVICE_KEY

MINIO_ENDPOINT=http://localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=YOUR_MINIO_PASSWORD
MINIO_BUCKET=hubspot-data

CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=8123
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=YOUR_CLICKHOUSE_PASSWORD
```

Replace the placeholder values with your local credentials.

**Security:** Never commit `.env`, API keys, passwords, or other secrets to GitHub.

### 5. Start MinIO and ClickHouse

Start the Docker services:

```powershell
docker compose up -d
```

Check their status:

```powershell
docker compose ps
```

### 6. Access the services

| Service | Local URL |
|---|---|
| MinIO Console | http://localhost:9001 |
| MinIO API | http://localhost:9000 |
| ClickHouse HTTP Interface | http://localhost:8123 |

Create the `hubspot-data` bucket in MinIO if it does not already exist.

### 7. Test the HubSpot connection

Run the existing connection test:

```powershell
python test_hubspot.py
```

A successful response should confirm that the HubSpot API is accessible and return the number of contacts retrieved.

## 📁 Project Structure

```text
hubspot-ingestion/
│
├── .dlt/
│   ├── config.toml
│   ├── secrets.toml
│   └── .sources
│
├── hubspot/
│   ├── __init__.py
│   ├── helpers.py
│   ├── settings.py
│   └── utils.py
│
├── .venv/
├── .env
├── .gitignore
├── docker-compose.yml
├── hubspot_pipeline.py
├── requirements.txt
├── test_hubspot.py
└── README.md
```

*The structure may change as development continues. Do not commit `.env`, `.venv/`, or files containing secrets.*

## 📂 Planned Data Storage Layout

Parquet files will be organized by resource and ingestion date:

```text
hubspot/
├── contacts/
│   └── year=YYYY/month=MM/
├── companies/
│   └── year=YYYY/month=MM/
├── deals/
│   └── year=YYYY/month=MM/
├── tickets/
│   └── year=YYYY/month=MM/
├── lineitems/
│   └── year=YYYY/month=MM/
├── engagements/
│   └── year=YYYY/month=MM/
├── pipelines/
│   └── year=YYYY/month=MM/
└── owners/
    └── year=YYYY/month=MM/
```

This is the intended layout; the final storage configuration is still to be implemented and tested.

## 🔄 Reliability and Incremental Processing

The planned pipeline will include:

- **Incremental ingestion:** Process records based on updated-at timestamps.
- **Persistent checkpoints:** Save pipeline state so processing can resume after interruption.
- **Crash recovery:** Resume interrupted ingestion without creating duplicate logical records.
- **Pause and resume:** Stop and restart ingestion safely.
- **Parallel processing:** Ingest supported resources concurrently.
- **Data validation:** Verify ingestion results and database records.

These features will be implemented and tested during development.

## 📊 Analytics

ClickHouse will be used to query ingested CRM data and build analytical views.

A planned analytical view will join:

- Deals
- Companies
- Pipelines

This will support reporting and analysis of CRM activity.

## 🧪 Testing Plan

- [x] HubSpot API connection test
- [x] Docker services started
- [x] ClickHouse connectivity verified
- [x] MinIO bucket created
- [ ] Configure `dlt` credentials
- [ ] Run the first `dlt` ingestion
- [ ] Store compressed Parquet files in MinIO
- [ ] Load data into ClickHouse
- [ ] Implement incremental checkpoints
- [ ] Test pause and resume
- [ ] Test forced-termination recovery
- [ ] Verify duplicate prevention
- [ ] Implement parallel ingestion
- [ ] Build analytical views

## 🔐 Security Notes

- Keep API tokens and passwords in local configuration files.
- Add `.env` and `.venv/` to `.gitignore`.
- Use least-privilege HubSpot permissions.
- Do not publish credentials in source code, logs, screenshots, or GitHub commits.

## 📌 Current Development Status

The initial development environment is configured. The HubSpot API connection has been tested successfully, and the MinIO and ClickHouse Docker services are running.

The next step is to configure the generated `dlt` HubSpot source and run the first ingestion test.

## 👨‍💻 Author

**Arman Ansary**

Data Engineering Project — HubSpot Data Ingestion Pipeline (BE-2)
