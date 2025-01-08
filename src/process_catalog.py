import argparse
import asyncio
import logging
import os
from typing import Optional

from dotenv import load_dotenv
# Import functions from existing scripts
from octogen_catalog import download_catalog
from load_to_db import load_parquet_files_to_sqlite
from index_catalog import create_whoosh_index

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def process_catalog(
    catalog: str,
    download_path: str,
    index_dir: Optional[str] = None,
    batch_size: int = 1000
) -> None:
    """Process a catalog through all three steps: download, load to DB, and index."""
    try:
        # Step 1: Download catalog
        logger.info(f"Step 1: Downloading catalog {catalog}")
        octogen_catalog_bucket = os.getenv("OCTOGEN_CATALOG_BUCKET_NAME")
        octogen_customer_name = os.getenv("OCTOGEN_CUSTOMER_NAME")
        
        await download_catalog(
            octogen_catalog_bucket=octogen_catalog_bucket,
            octogen_customer_name=octogen_customer_name,
            catalog=catalog,
            download_path=download_path
        )

        # Step 2: Load to database
        logger.info(f"Step 2: Loading catalog {catalog} to database")
        load_parquet_files_to_sqlite(download_path, catalog)

        # Step 3: Index the data
        logger.info(f"Step 3: Indexing catalog {catalog}")
        if not index_dir:
            index_dir = f"/tmp/whoosh/{catalog}"
        
        db_path = f"{catalog}_catalog.db"
        create_whoosh_index(db_path, index_dir, catalog, batch_size)

        logger.info(f"Successfully processed catalog {catalog}")

    except Exception as e:
        logger.error(f"Error processing catalog {catalog}: {e}")
        raise

async def main() -> None:
    parser = argparse.ArgumentParser(description="Process Octogen catalog: download, load to DB, and index")
    parser.add_argument(
        "--catalog",
        type=str,
        help="Name of the catalog to process",
        required=True
    )
    parser.add_argument(
        "--download",
        type=str,
        default="octogen-catalog-exchange",
        help="Path where catalog files will be downloaded"
    )
    parser.add_argument(
        "--index_dir",
        type=str,
        help="Directory to store the Whoosh index (default: /tmp/whoosh/<catalog>)"
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=1000,
        help="Batch size for indexing"
    )

    args = parser.parse_args()
    if not load_dotenv():
        logger.error("Failed to load .env file")
        logger.error(
            "Please see README.md for more information on how to set up the .env file."
        )
        return

    await process_catalog(
        catalog=args.catalog,
        download_path=args.download,
        index_dir=args.index_dir,
        batch_size=args.batch_size
    )

if __name__ == "__main__":
    asyncio.run(main()) 