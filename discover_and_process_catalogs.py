#!/usr/bin/env python3
"""
Script to discover and process catalogs from Google Cloud Storage.
This script is called by run_api_and_svelte_servers.sh before starting the servers.
"""

import asyncio
import logging
import os
from typing import List

from dotenv import load_dotenv
from google.cloud import storage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def discover_gcs_catalogs() -> List[str]:
    """Discover available catalogs in Google Cloud Storage."""
    # Load environment variables
    load_dotenv()

    # Check if required environment variables are set
    octogen_catalog_bucket = os.getenv("OCTOGEN_CATALOG_BUCKET_NAME")
    octogen_customer_name = os.getenv("OCTOGEN_CUSTOMER_NAME")

    if not octogen_catalog_bucket or not octogen_customer_name:
        logger.error("Missing required environment variables for GCS access")
        logger.error(
            "Please set OCTOGEN_CATALOG_BUCKET_NAME and OCTOGEN_CUSTOMER_NAME in the .env file"
        )
        return []

    try:
        # Connect to GCS
        storage_client = storage.Client()
        bucket = storage_client.bucket(octogen_catalog_bucket)

        # List all prefixes (directories) with the customer prefix
        customer_prefix = f"{octogen_customer_name}/"
        logger.info(
            f"Searching for catalogs in gs://{octogen_catalog_bucket}/{customer_prefix}"
        )

        # Get all prefixes (directories) with the customer prefix
        iterator = bucket.list_blobs(prefix=customer_prefix, delimiter="/")
        blobs = list(iterator)
        prefixes = list(iterator.prefixes)

        logger.info(f"Found {len(prefixes)} prefixes under {customer_prefix}")

        # Extract catalog names from prefixes like "shopagora/catalog=gymshark/"
        catalogs = []

        # Look for directories that start with catalog=
        for prefix in prefixes:
            if "catalog=" in prefix:
                parts = prefix.split("/")
                for part in parts:
                    if part.startswith("catalog="):
                        catalog_name = part.split("=")[1]
                        if catalog_name not in catalogs:
                            catalogs.append(catalog_name)
                            logger.info(
                                f"Found catalog in GCS: {catalog_name} at {prefix}"
                            )

        logger.info(f"Discovered {len(catalogs)} catalogs in GCS: {catalogs}")
        return catalogs

    except Exception as e:
        logger.error(f"Error discovering catalogs in GCS: {str(e)}")
        import traceback

        logger.error(traceback.format_exc())
        return []


async def process_catalog(catalog: str, download_path: str) -> bool:
    """Process a catalog from GCS."""
    try:
        # Load environment variables
        load_dotenv()
        octogen_catalog_bucket = os.getenv("OCTOGEN_CATALOG_BUCKET_NAME")
        octogen_customer_name = os.getenv("OCTOGEN_CUSTOMER_NAME")

        if not octogen_catalog_bucket or not octogen_customer_name:
            logger.error("Missing required environment variables for GCS access")
            return False

        logger.info(f"Processing catalog: {catalog}")

        # Import the necessary modules
        import src.load_to_db as load_to_db
        from src.download_catalog_files import download_catalog
        from src.index_catalog import create_whoosh_index
        from src.utils import get_catalog_db_path, get_latest_snapshot_path

        # Ensure download path exists
        os.makedirs(download_path, exist_ok=True)

        # Step 1: Download catalog
        logger.info(
            f"Step 1: Downloading catalog {catalog} from GCS bucket {octogen_catalog_bucket}"
        )
        await download_catalog(
            octogen_catalog_bucket=octogen_catalog_bucket,
            octogen_customer_name=octogen_customer_name,
            catalog=catalog,
            download_path=download_path,
        )

        # Get latest snapshot path
        catalog_path = download_path
        expected_catalog_suffix = f"catalog={catalog}"

        # Check if we need to navigate to the customer/catalog directory
        if not os.path.exists(
            os.path.join(catalog_path, expected_catalog_suffix)
        ) and not catalog_path.endswith(expected_catalog_suffix):
            catalog_path = os.path.join(
                download_path, octogen_customer_name, expected_catalog_suffix
            )
            logger.info(f"Using catalog path: {catalog_path}")

        # Find the latest snapshot directory
        try:
            catalog_path = get_latest_snapshot_path(catalog_path)
            logger.info(f"Using latest snapshot path: {catalog_path}")
        except ValueError as e:
            logger.error(f"Error finding snapshot directory: {str(e)}")
            logger.error(
                f"Available files in {catalog_path}: {os.listdir(catalog_path) if os.path.exists(catalog_path) else 'directory does not exist'}"
            )
            return False

        # Step 2: Load to database
        logger.info(
            f"Step 2: Loading catalog {catalog} to DuckDB database from {catalog_path}"
        )
        db_path = get_catalog_db_path(catalog, raise_if_not_found=False)
        logger.info(f"Using database path: {db_path}")
        load_to_db.load_products_to_db(catalog_path, catalog, create_if_missing=True)

        # Step 3: Index the data
        logger.info(f"Step 3: Indexing catalog {catalog}")
        index_dir = os.path.join("/tmp/whoosh", f"catalog={catalog}")
        create_whoosh_index(db_path, index_dir, catalog, 1000)

        logger.info(f"Successfully processed catalog: {catalog}")
        return True
    except Exception as e:
        logger.error(f"Error processing catalog {catalog}: {str(e)}")
        import traceback

        logger.error(traceback.format_exc())
        return False


async def get_local_catalogs() -> List[str]:
    """Get list of locally available catalogs."""
    base_dir = os.path.join(os.path.dirname(__file__))
    extension = "duckdb"
    catalogs = []

    for file in os.listdir(base_dir):
        if file.endswith(f"_catalog.{extension}"):
            catalog = file.replace(f"_catalog.{extension}", "")
            catalogs.append(catalog)
            logger.info(f"Found local catalog database: {file}")

    return catalogs


async def main():
    """Main function to discover and process catalogs."""
    # Get local catalogs
    local_catalogs = await get_local_catalogs()
    logger.info(f"Found {len(local_catalogs)} local catalogs: {local_catalogs}")

    # Get GCS catalogs
    gcs_catalogs = await discover_gcs_catalogs()
    logger.info(f"Found {len(gcs_catalogs)} GCS catalogs: {gcs_catalogs}")

    # Find missing catalogs
    missing_catalogs = [
        catalog for catalog in gcs_catalogs if catalog not in local_catalogs
    ]
    logger.info(f"Found {len(missing_catalogs)} missing catalogs: {missing_catalogs}")

    if not missing_catalogs:
        logger.info("No missing catalogs to process")
        return

    # Process missing catalogs
    download_path = "/tmp/octogen-catalog-exchange"
    success_count = 0

    for catalog in missing_catalogs:
        if await process_catalog(catalog, download_path):
            success_count += 1

    logger.info(
        f"Successfully processed {success_count} out of {len(missing_catalogs)} catalogs"
    )


if __name__ == "__main__":
    asyncio.run(main())
