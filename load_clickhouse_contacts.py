"""
Load Contacts Parquet data from MinIO into ClickHouse with Idempotency & Deduplication.

Features:
1. File-level Idempotency: Checks '_loaded_files' tracking table before loading.
2. Record-level Deduplication: ReplacingMergeTree engine + OPTIMIZE ensures no duplicate IDs.
"""

import clickhouse_connect


def get_client():
    return clickhouse_connect.get_client(
        host="localhost",
        port=8123,
        username="default",
        password="ClickHouseLocal123!",
    )


def ensure_tracking_table(client) -> None:
    client.command("""
    CREATE TABLE IF NOT EXISTS hubspot_dataset._loaded_files (
        file_path String,
        resource_name String,
        loaded_at DateTime DEFAULT now()
    ) ENGINE = ReplacingMergeTree()
    ORDER BY (resource_name, file_path)
    """)


def load_contacts_to_clickhouse(force_reload: bool = False) -> None:
    client = get_client()
    ensure_tracking_table(client)

    file_key = "hubspot/hubspot_dataset/contacts/year=2026/month=10/1793255688.8723178.8ed2553a92.parquet"
    resource = "contacts"

    # 1. File-level Idempotency check
    is_loaded = client.query(
        "SELECT count() FROM hubspot_dataset._loaded_files WHERE resource_name = %s AND file_path = %s",
        parameters=[resource, file_key],
    ).result_rows[0][0] > 0

    if is_loaded and not force_reload:
        print(f"[IDEMPOTENT SKIP] File '{file_key}' has already been processed.")
        count = client.query("SELECT count() FROM hubspot_dataset.contacts FINAL").result_rows[0][0]
        print(f"Current total unique contacts in ClickHouse: {count}")
        return

    # 2. Load data from MinIO into ClickHouse
    s3_url = f"http://minio:9000/hubspot-data/{file_key}"
    insert_sql = f"""
    INSERT INTO hubspot_dataset.contacts
    SELECT * FROM s3(
        '{s3_url}',
        'minioadmin',
        'LocalMinioPass123!',
        'Parquet'
    )
    """
    print(f"Loading '{file_key}' into ClickHouse...")
    client.command(insert_sql)

    # 3. Deduplicate rows using ReplacingMergeTree
    client.command("OPTIMIZE TABLE hubspot_dataset.contacts FINAL")

    # 4. Record loaded file into tracking table
    client.command(
        "INSERT INTO hubspot_dataset._loaded_files (file_path, resource_name) VALUES (%s, %s)",
        parameters=[file_key, resource],
    )

    total_rows = client.query("SELECT count() FROM hubspot_dataset.contacts FINAL").result_rows[0][0]
    print(f"[SUCCESS] File loaded and tracked. Total unique contacts: {total_rows}")


if __name__ == "__main__":
    import sys
    force = "--force" in sys.argv
    load_contacts_to_clickhouse(force_reload=force)
