"""
Unified Multi-Table ClickHouse Loader for HubSpot Data.

Features:
1. Dynamic Discovery: Automatically discovers Parquet files for all HubSpot resources in MinIO.
2. Auto Table Creation: Infers schema from Parquet file and creates ReplacingMergeTree tables.
3. File-level Idempotency: Checks and tracks loaded files in `_loaded_files` table.
4. Record Deduplication: Executes `OPTIMIZE TABLE ... FINAL` to remove duplicate IDs.
5. Multi-Table Support: contacts, companies, deals, owners, pipelines_deals.
"""

import os
import sys
from typing import List, Dict, Any
import clickhouse_connect
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "localhost")
CLICKHOUSE_PORT = int(os.getenv("CLICKHOUSE_PORT", "8123"))
CLICKHOUSE_USER = os.getenv("CLICKHOUSE_USER", "default")
CLICKHOUSE_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "ClickHouseLocal123!")

MINIO_INTERNAL_ENDPOINT = "http://minio:9000"
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "hubspot-data")
MINIO_USER = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_PASS = os.getenv("MINIO_SECRET_KEY", "LocalMinioPass123!")

RESOURCES = [
    {"name": "contacts", "order_by": "id"},
    {"name": "companies", "order_by": "id"},
    {"name": "deals", "order_by": "id"},
    {"name": "owners", "order_by": "id"},
    {"name": "pipelines_deals", "order_by": "id"},
]


def get_clickhouse_client():
    return clickhouse_connect.get_client(
        host=CLICKHOUSE_HOST,
        port=CLICKHOUSE_PORT,
        username=CLICKHOUSE_USER,
        password=CLICKHOUSE_PASSWORD,
    )


def ensure_database_and_tracking(client) -> None:
    client.command("CREATE DATABASE IF NOT EXISTS hubspot_dataset")
    client.command("""
    CREATE TABLE IF NOT EXISTS hubspot_dataset._loaded_files (
        file_path String,
        resource_name String,
        loaded_at DateTime DEFAULT now()
    ) ENGINE = ReplacingMergeTree()
    ORDER BY (resource_name, file_path)
    """)


def get_files_for_resource(client, resource_name: str) -> List[str]:
    """
    Uses ClickHouse's S3 function to discover existing Parquet files for this resource in MinIO.
    """
    wildcard_url = f"{MINIO_INTERNAL_ENDPOINT}/{MINIO_BUCKET}/hubspot/hubspot_dataset/{resource_name}/*/*/*.parquet"
    query = f"""
    SELECT DISTINCT _file
    FROM s3(
        '{wildcard_url}',
        '{MINIO_USER}',
        '{MINIO_PASS}',
        'Parquet'
    )
    """
    try:
        rows = client.query(query).result_rows
        return [r[0] for r in rows if r and r[0]]
    except Exception as e:
        # If no files exist for this resource yet
        return []


def ensure_table_exists(client, resource_name: str, order_by_col: str, sample_file_path: str) -> None:
    """
    Creates table dynamically matching the schema of the Parquet file if it doesn't exist.
    """
    create_sql = f"""
    CREATE TABLE IF NOT EXISTS hubspot_dataset.{resource_name}
    ENGINE = ReplacingMergeTree()
    ORDER BY {order_by_col}
    AS SELECT * FROM s3(
        '{MINIO_INTERNAL_ENDPOINT}/{MINIO_BUCKET}/{sample_file_path}',
        '{MINIO_USER}',
        '{MINIO_PASS}',
        'Parquet'
    ) WHERE 0
    """
    client.command(create_sql)


def load_resource(client, resource_cfg: Dict[str, str], force_reload: bool = False) -> None:
    resource_name = resource_cfg["name"]
    order_by_col = resource_cfg["order_by"]
    print(f"\n==========================================")
    print(f" Processing Resource: {resource_name.upper()} ")
    print(f"==========================================")

    # 1. Discover files in MinIO
    discovered_files = get_files_for_resource(client, resource_name)
    if not discovered_files:
        print(f"[INFO] No parquet files found in MinIO for resource: {resource_name}")
        return

    print(f"[FOUND] {len(discovered_files)} file(s) in MinIO.")

    # 2. Get already loaded files from tracking table
    loaded_files_res = client.query(
        "SELECT file_path FROM hubspot_dataset._loaded_files WHERE resource_name = %s",
        parameters=[resource_name],
    ).result_rows
    loaded_files = {r[0] for r in loaded_files_res}

    new_loads = 0
    for file_name in discovered_files:
        # Construct full S3 path key as tracked
        # _file returns filename (e.g. 1793255688.8723178.8ed2553a92.parquet) or relative path
        # Check if already processed
        if file_name in loaded_files and not force_reload:
            print(f"  [SKIP] File already loaded: {file_name}")
            continue

        file_url = f"{MINIO_INTERNAL_ENDPOINT}/{MINIO_BUCKET}/hubspot/hubspot_dataset/{resource_name}/*/*/{file_name}"

        # 3. Ensure table exists
        ensure_table_exists(client, resource_name, order_by_col, f"hubspot/hubspot_dataset/{resource_name}/*/*/{file_name}")

        # 4. Insert data from MinIO S3 into ClickHouse
        print(f"  [LOADING] Ingesting {file_name} into hubspot_dataset.{resource_name}...")
        insert_sql = f"""
        INSERT INTO hubspot_dataset.{resource_name}
        SELECT * FROM s3(
            '{file_url}',
            '{MINIO_USER}',
            '{MINIO_PASS}',
            'Parquet'
        )
        """
        client.command(insert_sql)

        # 5. Track loaded file
        client.command(
            "INSERT INTO hubspot_dataset._loaded_files (file_path, resource_name) VALUES (%s, %s)",
            parameters=[file_name, resource_name],
        )
        new_loads += 1

    # 6. Deduplicate table if any new data was loaded
    if new_loads > 0 or force_reload:
        print(f"  [DEDUPLICATION] Running OPTIMIZE TABLE hubspot_dataset.{resource_name} FINAL...")
        client.command(f"OPTIMIZE TABLE hubspot_dataset.{resource_name} FINAL")

    # 7. Summary count
    try:
        total_rows = client.query(f"SELECT count() FROM hubspot_dataset.{resource_name} FINAL").result_rows[0][0]
        print(f"[SUCCESS] Resource '{resource_name}' ready. Total unique records: {total_rows}")
    except Exception as e:
        print(f"[WARN] Could not retrieve row count: {e}")


def load_all_to_clickhouse(force_reload: bool = False) -> None:
    client = get_clickhouse_client()
    ensure_database_and_tracking(client)
    print("Database and tracking table verified.")

    for res in RESOURCES:
        load_resource(client, res, force_reload=force_reload)

    print("\n" + "="*50)
    print("ALL HUBSPOT RESOURCES PROCESSED SUCCESSFULLY!")
    print("="*50)


if __name__ == "__main__":
    force = "--force" in sys.argv
    load_all_to_clickhouse(force_reload=force)
