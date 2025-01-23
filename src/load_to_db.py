import argparse
import datetime
import glob
import json
import logging
import os

import duckdb
import numpy as np
import pandas as pd
from dotenv import load_dotenv

from utils import get_catalog_db_path

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.integer, np.int32, np.int64)):
            return int(obj)
        elif isinstance(obj, (np.float32, np.float64)):
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        return super(NumpyEncoder, self).default(obj)


def create_nested_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create a nested DataFrame with standardized columns regardless of input format.
    Handles both flattened and non-flattened data.
    """
    new_df = pd.DataFrame()
    flattened = is_data_flattened(df)

    if flattened:
        logger.info("Processing flattened data")
        # For flattened data, we need to create the extracted_product from all columns
        new_df["extracted_product"] = df.apply(
            lambda x: json.dumps(x.to_dict(), cls=NumpyEncoder), axis=1
        )
        new_df["catalog"] = df["catalog"]
        new_df["product_group_id"] = df["productGroupID"]
    else:
        logger.info("Processing non-flattened data")
        # For non-flattened data, we already have extracted_product
        new_df["extracted_product"] = df["extracted_product"].apply(
            lambda x: x if isinstance(x, str) else json.dumps(x, cls=NumpyEncoder)
        )
        new_df["catalog"] = df["catalog"]
        new_df["product_group_id"] = df["product_group_id"]

    # Verify all values are strings before returning
    if not new_df["extracted_product"].apply(lambda x: isinstance(x, str)).all():
        logger.error("Some extracted_product values are not strings!")
        non_string_samples = new_df[
            ~new_df["extracted_product"].apply(lambda x: isinstance(x, str))
        ]["extracted_product"].head()
        logger.error(f"Non-string samples: {non_string_samples}")
        # Force conversion to string
        new_df["extracted_product"] = new_df["extracted_product"].apply(
            lambda x: json.dumps(x, cls=NumpyEncoder) if not isinstance(x, str) else x
        )

    return new_df


def load_to_duckdb(
    conn: duckdb.DuckDBPyConnection,
    parquet_files: list[str],
    table_name: str,
    is_flattened: bool = False,
) -> tuple[int, int]:
    """Load parquet files into DuckDB database."""
    total_products = 0
    duplicates_skipped = 0

    if parquet_files:
        # Read first file and create table
        first_df = pd.read_parquet(parquet_files[0])
        if is_flattened:
            first_df = create_nested_dataframe(first_df)

        # Count total records in first file
        file_total = len(first_df)

        # Drop existing tables if they exist
        conn.execute(f"DROP TABLE IF EXISTS {table_name}")
        conn.execute(f"DROP TABLE IF EXISTS {table_name}_extracted")

        # Create temporary table for initial data
        conn.execute("DROP TABLE IF EXISTS temp_first")
        conn.execute("""
            CREATE TEMPORARY TABLE temp_first AS 
            SELECT *, 
                json_extract_string(extracted_product, 'productGroupID') as product_group_id,
                -- Pre-extract commonly used fields
                json_extract_string(extracted_product, 'id') as product_id,
                json_extract_string(extracted_product, '$.brand.name') as brand_name,
                json_extract_string(extracted_product, 'name') as name,
                json_extract_string(extracted_product, 'description') as description,
                json_extract_string(extracted_product, 'image') as product_image,
                TRY_CAST(json_extract_string(extracted_product, '$.price_info.price') AS FLOAT) as price,
                TRY_CAST(json_extract_string(extracted_product, '$.price_info.original_price') AS FLOAT) as original_price,
                TRY_CAST(json_extract_string(extracted_product, '$.rating.average_rating') AS FLOAT) as rating,
                TRY_CAST(json_extract_string(extracted_product, '$.rating.rating_count') AS INTEGER) as rating_count,
                -- json_extract_string(extracted_product, 'materials') as materials,
                -- json_extract_string(extracted_product, '$.audience.genders') as genders,
                -- json_extract_string(extracted_product, '$.audience.age_groups') as age_groups,
                -- json_extract_string(extracted_product, 'hasVariant') as variants_json,
                -- json_extract_string(extracted_product, 'additional_attributes') as additional_attributes_json
            FROM first_df
            WHERE json_extract_string(extracted_product, 'productGroupID') IS NOT NULL
        """)

        # Create main table with deduplicated data and extracted fields
        conn.execute(f"""
            CREATE TABLE {table_name}_extracted AS 
            SELECT DISTINCT ON (product_group_id) *
            FROM temp_first
            WHERE product_group_id IS NOT NULL
            ORDER BY product_group_id, extracted_product
        """)

        # Create original table with just the raw JSON for backwards compatibility
        conn.execute(f"""
            CREATE TABLE {table_name} AS 
            SELECT product_group_id, extracted_product
            FROM {table_name}_extracted
        """)

        initial_count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        duplicates_skipped += file_total - initial_count
        total_products += initial_count

        logger.info(
            f"Created tables {table_name} and {table_name}_extracted with schema from first file ({initial_count} products, {file_total - initial_count} duplicates skipped)"
        )

        # Add unique index
        conn.execute(f"""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_product_group_id 
            ON {table_name}_extracted (product_group_id)
        """)

        # Create additional attributes table
        # conn.execute(f"DROP TABLE IF EXISTS {table_name}_additional_attrs")
        # conn.execute(f"""
        #     CREATE TABLE {table_name}_additional_attrs AS
        #     WITH cleaned_json AS (
        #         SELECT
        #             CASE
        #                 WHEN additional_attributes_json IS NULL THEN ''
        #                 ELSE trim(both '{{}}' from additional_attributes_json)
        #             END as json_text,
        #             product_id
        #         FROM {table_name}_extracted
        #         WHERE additional_attributes_json IS NOT NULL
        #             AND additional_attributes_json != 'null'
        #             AND additional_attributes_json != '{{}}'
        #     ),
        #     split_pairs AS (
        #         SELECT
        #             trim(both '"' from split_part(value, ':', 1)) as attr_name,
        #             trim(both '"' from split_part(value, ':', 2)) as attr_value,
        #             c.product_id
        #         FROM cleaned_json c,
        #              (SELECT unnest(string_to_array(json_text, ',')) as value, product_id
        #               FROM cleaned_json) as pairs(value, product_id)
        #         WHERE value != ''
        #     )
        #     SELECT
        #         product_id,
        #         attr_name,
        #         attr_value
        #     FROM split_pairs
        #     WHERE attr_name != ''
        #         AND NOT attr_name LIKE 'style%'
        # """)

        # Create indexes for better query performance
        # conn.execute(f"""
        #     CREATE INDEX IF NOT EXISTS idx_{table_name}_additional_attrs_name
        #     ON {table_name}_additional_attrs (attr_name)
        # """)
        # conn.execute(f"""
        #     CREATE INDEX IF NOT EXISTS idx_{table_name}_additional_attrs_value
        #     ON {table_name}_additional_attrs (attr_value)
        # """)

        # Append remaining files
        for parquet_file in parquet_files[1:]:
            logger.info(f"Loading {parquet_file} into tables")
            try:
                df = pd.read_parquet(parquet_file)
                if is_flattened:
                    df = create_nested_dataframe(df)

                file_total = len(df)

                # Create temporary table with extracted fields
                conn.execute("DROP TABLE IF EXISTS temp_products")
                conn.execute("""
                    CREATE TEMPORARY TABLE temp_products AS 
                    SELECT *, 
                        json_extract_string(extracted_product, 'productGroupID') as product_group_id,
                        json_extract_string(extracted_product, 'id') as product_id,
                        json_extract_string(extracted_product, '$.brand.name') as brand_name,
                        json_extract_string(extracted_product, 'name') as name,
                        json_extract_string(extracted_product, 'description') as description,
                        json_extract_string(extracted_product, 'image') as product_image,
                        TRY_CAST(json_extract_string(extracted_product, '$.price_info.price') AS FLOAT) as price,
                        TRY_CAST(json_extract_string(extracted_product, '$.price_info.original_price') AS FLOAT) as original_price,
                        TRY_CAST(json_extract_string(extracted_product, '$.rating.average_rating') AS FLOAT) as rating,
                        TRY_CAST(json_extract_string(extracted_product, '$.rating.rating_count') AS INTEGER) as rating_count,
                        -- json_extract_string(extracted_product, 'materials') as materials,
                        -- json_extract_string(extracted_product, '$.audience.genders') as genders,
                        -- json_extract_string(extracted_product, '$.audience.age_groups') as age_groups,
                        -- json_extract_string(extracted_product, 'hasVariant') as variants_json,
                        -- json_extract_string(extracted_product, 'additional_attributes') as additional_attributes_json
                    FROM df
                    WHERE json_extract_string(extracted_product, 'productGroupID') IS NOT NULL
                """)

                # Count records before insertion
                pre_count = conn.execute(
                    f"SELECT COUNT(*) FROM {table_name}"
                ).fetchone()[0]

                # Modified insertion logic to handle duplicates gracefully
                conn.execute(f"""
                    BEGIN TRANSACTION;
                    
                    -- Insert into extracted table
                    INSERT INTO {table_name}_extracted
                    SELECT t.* 
                    FROM (
                        SELECT DISTINCT ON (product_group_id) *
                        FROM temp_products
                        ORDER BY product_group_id, extracted_product
                    ) t
                    WHERE NOT EXISTS (
                        SELECT 1 
                        FROM {table_name}_extracted m 
                        WHERE m.product_group_id = t.product_group_id
                    );

                    -- Insert into main table
                    INSERT INTO {table_name}
                    SELECT DISTINCT product_group_id, extracted_product
                    FROM temp_products t
                    WHERE NOT EXISTS (
                        SELECT 1 
                        FROM {table_name} m 
                        WHERE m.product_group_id = t.product_group_id
                    );
                    
                    COMMIT;
                """)

                # Count records after insertion
                post_count = conn.execute(
                    f"SELECT COUNT(*) FROM {table_name}"
                ).fetchone()[0]
                inserted = post_count - pre_count
                duplicates_skipped += file_total - inserted
                total_products += inserted

                logger.info(
                    f"Successfully loaded {inserted} rows ({file_total - inserted} duplicates skipped)"
                )
            except Exception as e:
                logger.error(f"Error loading {parquet_file}: {str(e)}")

        # Clean up temporary tables
        conn.execute("DROP TABLE IF EXISTS temp_first")
        conn.execute("DROP TABLE IF EXISTS temp_products")

    return total_products, duplicates_skipped


def load_products_to_db(
    download_path: str,
    catalog: str,
    create_if_missing: bool = False,
) -> None:
    """Load product parquet files into DuckDB database."""
    logger.info(
        f"Loading product parquet files from {download_path} for catalog {catalog}"
    )
    db_path = get_catalog_db_path(catalog, raise_if_not_found=not create_if_missing)
    logger.debug(f"Using database path: {db_path}")

    # Connect to database
    conn = duckdb.connect(db_path, config={"allow_unsigned_extensions": "true"})

    table_name = f"{os.path.splitext(catalog)[0].replace(os.sep, '_')}"
    parquet_files = glob.glob(
        os.path.join(download_path, "**/*.parquet"), recursive=True
    )

    try:
        if not parquet_files:
            logger.error(f"No parquet files found in {download_path}")
            return

        first_df = pd.read_parquet(parquet_files[0])
        is_flattened = is_data_flattened(first_df)
        logger.info(f"Detected {'flattened' if is_flattened else 'nested'} data format")

        total_products, duplicates_skipped = load_to_duckdb(
            conn, parquet_files, table_name, is_flattened
        )
        logger.info("Finished loading all product parquet files to DuckDB database.")
        logger.info(f"Total products loaded: {total_products}")
        logger.info(f"Duplicate records skipped: {duplicates_skipped}")
    finally:
        conn.close()


def load_crawls_to_db(
    download_path: str,
    catalog: str,
    create_if_missing: bool = False,
) -> None:
    """Load crawl data parquet files into DuckDB database."""
    logger.info(
        f"Loading crawl data parquet files from {download_path} for catalog {catalog}"
    )
    db_path = get_catalog_db_path(catalog, raise_if_not_found=not create_if_missing)
    logger.debug(f"Using database path: {db_path}")

    # Connect to database
    conn = duckdb.connect(db_path, config={"allow_unsigned_extensions": "true"})

    table_name = f"{os.path.splitext(catalog)[0].replace(os.sep, '_')}_crawls"
    parquet_files = glob.glob(
        os.path.join(download_path, "**/*.parquet"), recursive=True
    )

    try:
        if not parquet_files:
            logger.error(f"No parquet files found in {download_path}")
            return

        total_records, duplicates_skipped = load_crawl_data_to_duckdb(
            conn, parquet_files, table_name
        )
        logger.info("Finished loading all crawl data parquet files to DuckDB database.")
        logger.info(f"Total records loaded: {total_records}")
        logger.info(f"Duplicate records skipped: {duplicates_skipped}")
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Load Octogen catalog data to DuckDB")
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

    load_products_to_db(args.download, args.catalog, args.db_type)


def is_data_flattened(df: pd.DataFrame) -> bool:
    """
    Determine if a DataFrame contains flattened data by examining its structure.

    Returns:
        bool: True if data appears to be flattened, False otherwise
    """
    # Print columns for debugging
    if "extracted_product" in df.columns:
        # If it has extracted_product column, it's NOT flattened
        # logger.info("Found extracted_product column, data is NOT flattened")
        return False

    # If no extracted_product column, it IS flattened
    # logger.info("No extracted_product column found, data IS flattened")
    return True


def load_crawl_data_to_duckdb(
    conn: duckdb.DuckDBPyConnection,
    parquet_files: list[str],
    table_name: str,
) -> tuple[int, int]:
    """Load crawled product parquet files into DuckDB database."""
    total_records = 0
    duplicates_skipped = 0

    if not parquet_files:
        return total_records, duplicates_skipped

    # Read first file and create table
    first_df = pd.read_parquet(parquet_files[0])
    file_total = len(first_df)

    # Drop existing table if it exists
    conn.execute(f"DROP TABLE IF EXISTS {table_name}")

    # Create table with initial data - removed crawl_url from uniqueness constraints
    conn.execute(f"""
        CREATE TABLE {table_name} (
            crawl_id INTEGER PRIMARY KEY,
            catalog VARCHAR,
            product_url VARCHAR,
            crawl_url VARCHAR,
            page_content VARCHAR,
            crawl_timestamp BIGINT,
            crawl_source VARCHAR,
            api_source VARCHAR,
            octogen_catalog VARCHAR
        );

        CREATE SEQUENCE IF NOT EXISTS {table_name}_id_seq;
    """)

    # Modified initial data insertion - only using timestamp for ordering
    conn.execute(f"""
        INSERT INTO {table_name} (
            crawl_id,
            catalog,
            product_url,
            crawl_url,
            page_content,
            crawl_timestamp,
            crawl_source,
            api_source,
            octogen_catalog
        )
        SELECT 
            nextval('{table_name}_id_seq'),
            catalog,
            product_url,
            crawl_url,
            page_content,
            crawl_timestamp,
            crawl_source,
            api_source,
            octogen_catalog
        FROM (
            SELECT *
            FROM first_df
            ORDER BY crawl_timestamp DESC
        );
    """)

    initial_count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    duplicates_skipped += file_total - initial_count
    total_records += initial_count

    logger.info(
        f"Created table {table_name} with schema from first file ({initial_count} records, {file_total - initial_count} duplicates skipped)"
    )

    # Create indexes for better query performance
    conn.execute(f"""
        CREATE INDEX IF NOT EXISTS idx_{table_name}_crawl_url 
        ON {table_name} (crawl_url)
    """)
    conn.execute(f"""
        CREATE INDEX IF NOT EXISTS idx_{table_name}_timestamp 
        ON {table_name} (crawl_timestamp)
    """)

    # Append remaining files
    for parquet_file in parquet_files[1:]:
        logger.info(f"Loading {parquet_file}")
        try:
            df = pd.read_parquet(parquet_file)
            file_total = len(df)

            # Count records before insertion
            pre_count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]

            # Modified insert query - removed crawl_url uniqueness check
            conn.execute(f"""
                INSERT INTO {table_name} (
                    crawl_id,
                    catalog,
                    product_url,
                    crawl_url,
                    page_content,
                    crawl_timestamp,
                    crawl_source,
                    api_source,
                    octogen_catalog
                )
                SELECT 
                    nextval('{table_name}_id_seq'),
                    t.catalog,
                    t.product_url,
                    t.crawl_url,
                    t.page_content,
                    t.crawl_timestamp,
                    t.crawl_source,
                    t.api_source,
                    t.octogen_catalog
                FROM (
                    SELECT *
                    FROM df
                    ORDER BY crawl_timestamp DESC
                ) t
                WHERE NOT EXISTS (
                    SELECT 1 
                    FROM {table_name} m 
                    WHERE m.crawl_timestamp = t.crawl_timestamp
                );
            """)

            # Count records after insertion
            post_count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[
                0
            ]
            inserted = post_count - pre_count
            duplicates_skipped += file_total - inserted
            total_records += inserted

            logger.info(
                f"Successfully loaded {inserted} rows ({file_total - inserted} duplicates skipped)"
            )
        except Exception as e:
            logger.error(f"Error loading {parquet_file}: {str(e)}")

    return total_records, duplicates_skipped


if __name__ == "__main__":
    main()
