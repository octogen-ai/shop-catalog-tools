import argparse
import glob
import logging
import os
import sqlite3
from typing import Any

from dotenv import load_dotenv
import pandas as pd

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def load_parquet_files_to_sqlite(download_path: str, catalog: str, ) -> None:
    """Load all parquet files from the download path into a SQLite database."""

    db_path = os.path.join(os.path.dirname(__file__), "..", f"{catalog}_catalog.db")
    logger.info(f"Loading parquet files from {download_path} into {db_path}")
    
    # Connect to SQLite database
    conn = sqlite3.connect(db_path)
    
    table_name = os.path.splitext(catalog)[0].replace(os.sep, "_")
    # Find all parquet files recursively
    parquet_files = glob.glob(os.path.join(download_path, "**/*.parquet"), recursive=True)
    
    total_products = 0
    duplicates_skipped = 0
    
    # Create table with first file
    if parquet_files:
        first_df = pd.read_parquet(parquet_files[0])
        print(first_df.columns)
        first_df.to_sql(table_name, conn, if_exists="replace", index=False)
        total_products += len(first_df)
        logger.info(f"Created table {table_name} with schema from first file ({len(first_df)} products)")
        
        # Add unique constraint on productGroupID
        cursor = conn.cursor()
        cursor.execute(f"""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_product_group_id 
            ON {table_name} (json_extract(extracted_product, '$.productGroupID'))
            WHERE json_extract(extracted_product, '$.productGroupID') IS NOT NULL
        """)
        conn.commit()
        parquet_files = parquet_files[1:]  # Remove first file from list
    
    # Append remaining files
    for parquet_file in parquet_files:
        logger.info(f"Loading {parquet_file} into table {table_name}")
        
        try:
            # Read parquet file
            df = pd.read_parquet(parquet_file)
            
            # Write to SQLite, ignoring duplicates
            df.to_sql(table_name, conn, if_exists="append", index=False)
            total_products += len(df)
            logger.info(f"Successfully loaded {len(df)} rows into {table_name}")
            
        except sqlite3.IntegrityError as e:
            # Count this as a duplicate and continue
            duplicates_skipped += 1
            logger.warning(f"Skipped duplicate product group in {parquet_file}: {str(e)}")
        except Exception as e:
            logger.error(f"Error loading {parquet_file}: {str(e)}")
    
    conn.close()
    logger.info(f"Finished loading all parquet files to SQLite database.")
    logger.info(f"Total products loaded: {total_products}")
    logger.info(f"Duplicate products skipped: {duplicates_skipped}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Load Octogen catalog data to SQLite")
    parser.add_argument(
        "--catalog",
        type=str,
        help="Name of the catalog to load",
        required=True,
    )
    parser.add_argument(
        "--download",
        type=str,
        help="Path to the downloaded parquet files",
        required=True,
    )

    args = parser.parse_args()
    
    if not os.path.exists(args.download):
        logger.error(f"Download path {args.download} does not exist")
        return
    if not load_dotenv():
        logger.error("Failed to load .env file")
        logger.error(
            "Please see README.md for more information on how to set up the .env file."
        )
        return


    load_parquet_files_to_sqlite(args.download, args.catalog)


if __name__ == "__main__":
    main()
