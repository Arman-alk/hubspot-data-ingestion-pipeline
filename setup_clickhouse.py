"""
Setup ClickHouse Database and Contacts Table.
Infers schema directly from the Parquet file in MinIO and uses
ReplacingMergeTree(order by id) to prevent logical duplicates.
"""

import clickhouse_connect


def setup_clickhouse() -> None:
    # 1. Connect to local ClickHouse server
    client = clickhouse_connect.get_client(
        host="localhost",
        port=8123,
        username="default",
        password="ClickHouseLocal123!",
    )

    # 2. Ensure database exists
    client.command("CREATE DATABASE IF NOT EXISTS hubspot_dataset")
    print("Database 'hubspot_dataset' verified.")

    # 3. Drop old dummy table if it exists (which only had id, properties)
    client.command("DROP TABLE IF EXISTS hubspot_dataset.contacts")
    print("Dropped old dummy 'hubspot_dataset.contacts' table.")

    # 4. Create table with exact Parquet schema using ReplacingMergeTree
    # MinIO is accessible inside Docker network at http://minio:9000
    create_table_sql = """
    CREATE TABLE hubspot_dataset.contacts
    ENGINE = ReplacingMergeTree()
    ORDER BY id
    AS SELECT * FROM s3(
        'http://minio:9000/hubspot-data/hubspot/hubspot_dataset/contacts/year=2026/month=10/1793255688.8723178.8ed2553a92.parquet',
        'minioadmin',
        'LocalMinioPass123!',
        'Parquet'
    ) WHERE 0
    """
    client.command(create_table_sql)
    print("Created new 'hubspot_dataset.contacts' table matching Parquet schema.")

    # 5. Verify the created schema
    columns = client.query("DESCRIBE TABLE hubspot_dataset.contacts").result_rows
    print(f"Total Columns in table: {len(columns)}")
    print("Sample Columns:")
    for col in columns[:10]:
        print(f"  - {col[0]}: {col[1]}")


if __name__ == "__main__":
    setup_clickhouse()
