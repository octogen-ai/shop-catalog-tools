import argparse
import asyncio
import os
from typing import Optional

import structlog
from dotenv import load_dotenv

import load_to_db

# Import functions from existing scripts
from download_catalog_files import download_catalog
from index_catalog import create_whoosh_index
from utils import configure_logging, get_catalog_db_path, get_latest_snapshot_path

# Configure logging
configure_logging(debug=False, log_to_console=True)
logger = structlog.get_logger(__name__)


async def process_catalog(
    catalog: str,
    download_to: str,
    index_dir: Optional[str] = None,
    batch_size: int = 1000,
    read_from_local_files: bool = False,
    crawl_sources_dir: Optional[str] = None,
) -> None:
    """Process a catalog through all three steps: download, load to DB, and index."""
    octogen_catalog_bucket = os.getenv("OCTOGEN_CATALOG_BUCKET_NAME")
    octogen_customer_name = os.getenv("OCTOGEN_CUSTOMER_NAME")
    original_download_to: str = download_to
    # Ensure download_to ends with catalog={catalog}
    try:
        # Step 1: Download catalog
        if read_from_local_files:
            # Find the latest snapshot directory
            download_to = get_latest_snapshot_path(download_to)
            if not download_to:
                raise ValueError(f"No snapshot directories found in {download_to}")

            logger.info(
                f"Step 1: Reading catalog {catalog} from local files in {download_to}"
            )
        else:
            logger.info(f"Step 1: Downloading catalog {catalog}")
            await download_catalog(
                octogen_catalog_bucket=octogen_catalog_bucket,
                octogen_customer_name=octogen_customer_name,
                catalog=catalog,
                download_path=download_to,
            )
        # Only modify path if no parquet files found in current download_to
        if not any(f.endswith(".parquet") for f in os.listdir(download_to)):
            expected_catalog_suffix = f"catalog={catalog}"
            if not download_to.endswith(expected_catalog_suffix):
                download_to = os.path.join(
                    download_to, octogen_customer_name, expected_catalog_suffix
                )
        download_to = get_latest_snapshot_path(download_to)

        # Step 2: Load to database
        logger.info(
            f"Step 2: Loading catalog {catalog} to DuckDB database. From parquet files in {download_to}"
        )
        db_path = get_catalog_db_path(catalog, raise_if_not_found=False)
        logger.debug(f"Using database path: {db_path}")
        load_to_db.load_products_to_db(download_to, catalog, create_if_missing=True)
        if crawl_sources_dir:
            print(f"crawl_sources_dir: {crawl_sources_dir}")
            print(f"original_download_to: {original_download_to}")
            print(f"download_to: {download_to}")
            crawl_sources_dir = download_to.replace(
                original_download_to, crawl_sources_dir
            )
            logger.info(
                f"Step 2.1: Processing crawled sources in {crawl_sources_dir} and linking to catalog {catalog}"
            )
            load_to_db.load_crawls_to_db(
                crawl_sources_dir, catalog, create_if_missing=True
            )
        # Step 3: Index the data
        logger.info(f"Step 3: Indexing catalog {catalog}")

        create_whoosh_index(db_path, index_dir, catalog, batch_size)

        logger.info(f"Successfully processed catalog {catalog}")

    except Exception as e:
        logger.error(f"Error processing catalog {catalog}: {e}")
        raise


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Process Octogen catalog: download, load to DB, and index"
    )
    parser.add_argument(
        "--catalog", type=str, help="Name of the catalog to process", required=True
    )
    parser.add_argument(
        "--download",
        type=str,
        required=False,
        default="/tmp/octogen-catalog-exchange",
        help="Path where catalog files will be downloaded",
    )
    parser.add_argument(
        "--index_dir",
        type=str,
        default="/tmp/whoosh",
        help="Directory to store the Whoosh index (default: /tmp/whoosh/<catalog>)",
    )
    parser.add_argument(
        "--batch_size", type=int, default=1000, help="Batch size for indexing"
    )
    parser.add_argument(
        "--local",
        action="store_true",
        default=False,
        help="Read catalog from local files instead of downloading from GCS",
    )
    parser.add_argument(
        "--crawl-sources-dir",
        type=str,
        help="Folder for crawled sources. Those get processed, so that we can link to them. ",
    )

    args = parser.parse_args()
    if not load_dotenv():
        logger.error("Failed to load .env file")
        logger.error(
            "Please see README.md for more information on how to set up the .env file."
        )
        return

    download_to: str = args.download
    if args.local:
        download_to = os.path.join(download_to, f"catalog={args.catalog}")
        if args.crawl_sources_dir:
            args.crawl_sources_dir = os.path.join(
                args.crawl_sources_dir, f"catalog={args.catalog}"
            )

    await process_catalog(
        catalog=args.catalog,
        download_to=download_to,
        index_dir=args.index_dir,
        batch_size=args.batch_size,
        read_from_local_files=args.local,
        crawl_sources_dir=args.crawl_sources_dir,
    )


if __name__ == "__main__":
    asyncio.run(main())
