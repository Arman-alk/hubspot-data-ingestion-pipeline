"""
Master End-to-End HubSpot Ingestion & ClickHouse Warehouse Automation Script.

Workflow:
1. Stage 1: Incremental Data Extraction from HubSpot CRM -> MinIO Data Lake (Parquet).
2. Stage 2: S3-to-ClickHouse Ingestion with Idempotency & Deduplication.
3. Stage 3: Analytical Views Creation & Health Check.
"""

import sys
import time
import logging
from datetime import datetime

# Setup structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("pipeline_execution.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("HubSpotPipeline")


def run_full_pipeline() -> None:
    start_time = time.time()
    logger.info("==========================================================")
    logger.info(" STARTING HUBSPOT END-TO-END DATA PIPELINE ")
    logger.info("==========================================================")

    # ----------------------------------------------------
    # STAGE 1: HubSpot -> MinIO Ingestion (DLT)
    # ----------------------------------------------------
    logger.info("[STAGE 1/3] Extracting HubSpot CRM Data to MinIO (Parquet)...")
    try:
        from hubspot_pipeline import load_crm_data
        load_crm_data()
        logger.info("[STAGE 1/3 COMPLETED] Ingestion to MinIO finished successfully.")
    except Exception as e:
        logger.error(f"[STAGE 1 FAILED] HubSpot Ingestion failed: {e}", exc_info=True)
        sys.exit(1)

    # ----------------------------------------------------
    # STAGE 2: MinIO -> ClickHouse Ingestion (ReplacingMergeTree)
    # ----------------------------------------------------
    logger.info("[STAGE 2/3] Loading Parquet files into ClickHouse tables...")
    try:
        from load_all_to_clickhouse import load_all_to_clickhouse
        load_all_to_clickhouse()
        logger.info("[STAGE 2/3 COMPLETED] ClickHouse multi-table loading finished.")
    except Exception as e:
        logger.error(f"[STAGE 2 FAILED] ClickHouse Loading failed: {e}", exc_info=True)
        sys.exit(1)

    # ----------------------------------------------------
    # STAGE 3: Analytical Views & Validation
    # ----------------------------------------------------
    logger.info("[STAGE 3/3] Creating and refreshing analytical views...")
    try:
        from create_analytical_views import create_views
        create_views()
        logger.info("[STAGE 3/3 COMPLETED] Analytical views verified.")
    except Exception as e:
        logger.error(f"[STAGE 3 FAILED] Analytical views creation failed: {e}", exc_info=True)
        sys.exit(1)

    elapsed_time = round(time.time() - start_time, 2)
    logger.info("==========================================================")
    logger.info(f" PIPELINE FINISHED SUCCESSFULLY IN {elapsed_time} SECONDS! ")
    logger.info("==========================================================")


if __name__ == "__main__":
    run_full_pipeline()
