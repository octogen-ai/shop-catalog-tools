import argparse
import glob
import logging
import os
import sqlite3
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def load_parquet_files_to_sqlite(download_path: str, catalog: str) -> None:
    """Load all parquet files from the download path into a SQLite database."""
    db_path = f"{catalog}_catalog.db"
    logger.info(f"Loading parquet files from {download_path} into {db_path}")
    
    # Connect to SQLite database
    conn = sqlite3.connect(db_path)
    
    table_name = os.path.splitext(catalog)[0].replace(os.sep, "_")
    # Find all parquet files recursively
    parquet_files = glob.glob(os.path.join(download_path, "**/*.parquet"), recursive=True)
    
    for parquet_file in parquet_files:
        # Get the relative path without extension as table name
        rel_path = os.path.relpath(parquet_file, download_path)
        
        logger.info(f"Loading {parquet_file} into table {table_name}")
        
        try:
            # Read parquet file
            df = pd.read_parquet(parquet_file)
            
            # Write to SQLite
            df.to_sql(table_name, conn, if_exists="replace", index=False)
            logger.info(f"Successfully loaded {len(df)} rows into {table_name}")
            
        except Exception as e:
            logger.error(f"Error loading {parquet_file}: {str(e)}")
    
    conn.close()
    logger.info("Finished loading all parquet files to SQLite database")


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
        help="Path to downloaded parquet files",
        required=True,
    )

    args = parser.parse_args()
    
    if not os.path.exists(args.download):
        logger.error(f"Download path {args.download} does not exist")
        return
        
    load_parquet_files_to_sqlite(args.download, args.catalog)


if __name__ == "__main__":
    main()
