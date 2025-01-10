import argparse
import asyncio
import logging
import os
from typing import Optional

from dotenv import load_dotenv

from index_catalog import create_whoosh_index
from load_to_db import load_parquet_files_to_db

# Import functions from existing scripts
from octogen_catalog import download_catalog

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def process_catalog(
    catalog: str,
    download_to: str,
    index_dir: Optional[str] = None,
    batch_size: int = 1000,
    read_from_local_files: bool = False,
    db_type: str = "sqlite",
    is_flattened: bool = True,
) -> None:
    """Process a catalog through all three steps: download, load to DB, and index."""
    try:
        # Step 1: Download catalog
        if read_from_local_files:
            logger.info(f"Step 1: Reading catalog {catalog} from local files")
        else:
            logger.info(f"Step 1: Downloading catalog {catalog}")
            octogen_catalog_bucket = os.getenv("OCTOGEN_CATALOG_BUCKET_NAME")
            octogen_customer_name = os.getenv("OCTOGEN_CUSTOMER_NAME")

            if octogen_customer_name not in download_to:
                download_to = os.path.join(
                    download_to, octogen_customer_name, f"catalog={catalog}"
                )
            await download_catalog(
                octogen_catalog_bucket=octogen_catalog_bucket,
                octogen_customer_name=octogen_customer_name,
                catalog=catalog,
                download_path=download_to,
            )

        # Step 2: Load to database
        logger.info(f"Step 2: Loading catalog {catalog} to {db_type} database")
        load_parquet_files_to_db(download_to, catalog, db_type, is_flattened)

        # Step 3: Index the data
        logger.info(f"Step 3: Indexing catalog {catalog}")
        if not index_dir:
            index_dir = f"/tmp/whoosh/{catalog}"

        db_path = f"{catalog}_catalog.{db_type}"
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
        default="octogen-catalog-exchange",
        help="Path where catalog files will be downloaded",
    )
    parser.add_argument(
        "--index_dir",
        type=str,
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
        "--db-type",
        type=str,
        choices=["sqlite", "duckdb"],
        default="sqlite",
        help="Database type to use (sqlite or duckdb)",
    )
    parser.add_argument(
        "--is-flattened",
        action="store_true",
        help="Whether the catalog is flattened",
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
        if not download_to.endswith(f"/{args.catalog}") or not download_to.endswith(
            f"/{args.catalog}/"
        ):
            download_to = os.path.join(download_to, f"{args.catalog}")
    else:
        octogen_customer_name = os.getenv("OCTOGEN_CUSTOMER_NAME")

        if octogen_customer_name not in download_to:
            download_to = os.path.join(
                download_to, octogen_customer_name, f"catalog={args.catalog}"
            )

    await process_catalog(
        catalog=args.catalog,
        download_to=download_to,
        index_dir=args.index_dir,
        batch_size=args.batch_size,
        read_from_local_files=args.local,
        db_type=args.db_type,
        is_flattened=args.is_flattened,
    )


if __name__ == "__main__":
    asyncio.run(main())
