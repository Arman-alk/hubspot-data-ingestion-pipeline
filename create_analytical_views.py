"""
Create Analytical Views in ClickHouse for HubSpot Data.

Curated Views Created:
1. v_hubspot_deal_pipeline (Mandatory Requirement):
   Combines Deals, Companies, and Pipelines for instant business reporting.
2. v_deal_pipeline_summary:
   Aggregates deals by stage, pipeline, total value, and deal counts.
3. v_company_deal_analytics:
   Aggregates deal metrics by company.
4. v_contact_overview:
   Consolidated view of contacts and recent modifications.
"""

import os
import clickhouse_connect
from dotenv import load_dotenv

load_dotenv()

CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "localhost")
CLICKHOUSE_PORT = int(os.getenv("CLICKHOUSE_PORT", "8123"))
CLICKHOUSE_USER = os.getenv("CLICKHOUSE_USER", "default")
CLICKHOUSE_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "ClickHouseLocal123!")


def ensure_base_tables_exist(client) -> None:
    """Ensure all base tables exist so views can be created even if some resources had 0 records."""
    client.command("""
    CREATE TABLE IF NOT EXISTS hubspot_dataset.deals (
        id String,
        dealname Nullable(String),
        dealstage Nullable(String),
        amount Nullable(String),
        pipeline Nullable(String),
        createdate Nullable(String),
        closedate Nullable(String),
        hs_lastmodifieddate Nullable(String)
    ) ENGINE = ReplacingMergeTree() ORDER BY id
    """)

    client.command("""
    CREATE TABLE IF NOT EXISTS hubspot_dataset.companies (
        id String,
        name Nullable(String),
        domain Nullable(String),
        createdate Nullable(String),
        hs_lastmodifieddate Nullable(String)
    ) ENGINE = ReplacingMergeTree() ORDER BY id
    """)

    client.command("""
    CREATE TABLE IF NOT EXISTS hubspot_dataset.pipelines_deals (
        id String,
        label Nullable(String),
        displayOrder Nullable(Int64),
        created_at Nullable(String),
        updated_at Nullable(String)
    ) ENGINE = ReplacingMergeTree() ORDER BY id
    """)


def create_views() -> None:
    client = clickhouse_connect.get_client(
        host=CLICKHOUSE_HOST,
        port=CLICKHOUSE_PORT,
        username=CLICKHOUSE_USER,
        password=CLICKHOUSE_PASSWORD,
    )

    print("Connected to ClickHouse. Ensuring base tables and creating curated analytical views...")
    ensure_base_tables_exist(client)

    # 1. MANDATORY VIEW: v_hubspot_deal_pipeline (Deals + Companies + Pipelines)
    # Using subqueries with FINAL ensures 100% compatibility across all ClickHouse versions
    view_hubspot_deal_pipeline = """
    CREATE OR REPLACE VIEW hubspot_dataset.v_hubspot_deal_pipeline AS
    SELECT
        d.id AS deal_id,
        d.dealname AS deal_name,
        d.dealstage AS deal_stage,
        toFloat64OrZero(d.amount) AS deal_amount,
        d.createdate AS deal_created_at,
        d.closedate AS deal_close_date,
        c.id AS company_id,
        c.name AS company_name,
        c.domain AS company_domain,
        p.id AS pipeline_id,
        p.label AS pipeline_label
    FROM (SELECT * FROM hubspot_dataset.deals FINAL) AS d
    LEFT JOIN (SELECT * FROM hubspot_dataset.companies FINAL) AS c
        ON d.id = c.id
    LEFT JOIN (SELECT * FROM hubspot_dataset.pipelines_deals FINAL) AS p
        ON d.pipeline = p.id
    """
    client.command(view_hubspot_deal_pipeline)
    print("  [OK] Created mandatory view: hubspot_dataset.v_hubspot_deal_pipeline")

    # 2. View: Deals Summary by Pipeline and Stage
    view_pipeline_summary = """
    CREATE OR REPLACE VIEW hubspot_dataset.v_deal_pipeline_summary AS
    SELECT
        d.pipeline,
        d.dealstage,
        count(d.id) AS total_deals,
        sum(toFloat64OrZero(d.amount)) AS total_deal_amount,
        avg(toFloat64OrZero(d.amount)) AS avg_deal_amount,
        min(d.createdate) AS earliest_deal,
        max(d.createdate) AS latest_deal
    FROM (SELECT * FROM hubspot_dataset.deals FINAL) AS d
    GROUP BY
        d.pipeline,
        d.dealstage
    """
    client.command(view_pipeline_summary)
    print("  [OK] Created view: hubspot_dataset.v_deal_pipeline_summary")

    # 3. View: Company Deal Analytics
    view_company_deals = """
    CREATE OR REPLACE VIEW hubspot_dataset.v_company_deal_analytics AS
    SELECT
        c.id AS company_id,
        c.name AS company_name,
        c.domain AS company_domain,
        count(d.id) AS total_deals,
        sum(toFloat64OrZero(d.amount)) AS total_revenue_potential,
        max(d.createdate) AS last_deal_date
    FROM (SELECT * FROM hubspot_dataset.companies FINAL) AS c
    LEFT JOIN (SELECT * FROM hubspot_dataset.deals FINAL) AS d
        ON c.id = d.id
    GROUP BY
        c.id,
        c.name,
        c.domain
    """
    client.command(view_company_deals)
    print("  [OK] Created view: hubspot_dataset.v_company_deal_analytics")

    # 4. View: Contact Activity Tracking
    view_contacts = """
    CREATE OR REPLACE VIEW hubspot_dataset.v_contact_overview AS
    SELECT
        id AS contact_id,
        firstname,
        lastname,
        email,
        createdate,
        lastmodifieddate
    FROM hubspot_dataset.contacts FINAL
    """
    client.command(view_contacts)
    print("  [OK] Created view: hubspot_dataset.v_contact_overview")

    print("\nAll analytical views created successfully!")


if __name__ == "__main__":
    create_views()
