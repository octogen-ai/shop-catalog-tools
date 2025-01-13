import argparse
import datetime
import glob
import json
import logging
import os
import sqlite3

import duckdb
import numpy as np
import pandas as pd
from dotenv import load_dotenv

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


def load_to_sqlite(
    conn: sqlite3.Connection,
    parquet_files: list[str],
    table_name: str,
    is_flattened: bool = False,
) -> tuple[int, int]:
    """Load parquet files into SQLite database."""
    total_products = 0
    duplicates_skipped = 0

    if parquet_files:
        # Create table with first file
        first_df = pd.read_parquet(parquet_files[0])
        if is_flattened:
            first_df = create_nested_dataframe(first_df)
        first_df.to_sql(table_name, conn, if_exists="replace", index=False)

        cursor = conn.cursor()
        initial_count = cursor.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[
            0
        ]
        total_products += initial_count
        logger.info(
            f"Created table {table_name} with schema from first file ({initial_count} products)"
        )

        # Create a temporary table for the product group IDs
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name}_group_ids AS
            SELECT DISTINCT json_extract(extracted_product, '$.productGroupID') as product_group_id
            FROM {table_name}
            WHERE json_extract(extracted_product, '$.productGroupID') IS NOT NULL
        """)
        conn.commit()

        # Append remaining files
        for parquet_file in parquet_files[1:]:
            logger.info(f"Loading {parquet_file} into table {table_name}")
            try:
                df = pd.read_parquet(parquet_file)
                if is_flattened:
                    df = create_nested_dataframe(df)

                # Count total records in the new file
                file_total = len(df)

                # Use temporary table for deduplication
                temp_table = f"{table_name}_temp"
                df.to_sql(temp_table, conn, if_exists="replace", index=False)

                # Get count before insertion
                pre_count = cursor.execute(
                    f"SELECT COUNT(*) FROM {table_name}"
                ).fetchone()[0]

                # Insert non-duplicate records
                cursor.execute(f"""
                    INSERT INTO {table_name}
                    SELECT t.*
                    FROM {temp_table} t
                    WHERE NOT EXISTS (
                        SELECT 1 
                        FROM {table_name}_group_ids g
                        WHERE g.product_group_id = json_extract(t.extracted_product, '$.productGroupID')
                    )
                """)

                # Get count after insertion
                post_count = cursor.execute(
                    f"SELECT COUNT(*) FROM {table_name}"
                ).fetchone()[0]
                inserted = post_count - pre_count
                duplicates_skipped += file_total - inserted

                # Update group IDs table
                cursor.execute(f"""
                    INSERT INTO {table_name}_group_ids
                    SELECT DISTINCT json_extract(extracted_product, '$.productGroupID') as product_group_id
                    FROM {temp_table}
                    WHERE json_extract(extracted_product, '$.productGroupID') IS NOT NULL
                    AND product_group_id NOT IN (SELECT product_group_id FROM {table_name}_group_ids)
                """)

                # Drop temporary table
                cursor.execute(f"DROP TABLE IF EXISTS {temp_table}")
                conn.commit()

                total_products += inserted
                logger.info(
                    f"Successfully loaded {inserted} rows into {table_name} ({file_total - inserted} duplicates skipped)"
                )
            except sqlite3.IntegrityError as e:
                duplicates_skipped += 1
                logger.warning(
                    f"Skipped duplicate product group in {parquet_file}: {str(e)}"
                )
            except Exception as e:
                logger.error(f"Error loading {parquet_file}: {str(e)}")

        # Clean up
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}_group_ids")
        conn.commit()

    return total_products, duplicates_skipped


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
                json_extract_string(extracted_product, 'materials') as materials,
                json_extract_string(extracted_product, '$.audience.genders') as genders,
                json_extract_string(extracted_product, '$.audience.age_groups') as age_groups,
                json_extract_string(extracted_product, 'hasVariant') as variants_json,
                json_extract_string(extracted_product, 'additional_attributes') as additional_attributes_json
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
        conn.execute(f"DROP TABLE IF EXISTS {table_name}_additional_attrs")
        conn.execute(f"""
            CREATE TABLE {table_name}_additional_attrs AS
            WITH cleaned_json AS (
                SELECT 
                    CASE 
                        WHEN additional_attributes_json IS NULL THEN ''
                        ELSE trim(both '{{}}' from additional_attributes_json)
                    END as json_text,
                    product_id
                FROM {table_name}_extracted
                WHERE additional_attributes_json IS NOT NULL
                    AND additional_attributes_json != 'null'
                    AND additional_attributes_json != '{{}}'
            ),
            split_pairs AS (
                SELECT 
                    trim(both '"' from split_part(value, ':', 1)) as attr_name,
                    trim(both '"' from split_part(value, ':', 2)) as attr_value,
                    c.product_id
                FROM cleaned_json c,
                     (SELECT unnest(string_to_array(json_text, ',')) as value, product_id 
                      FROM cleaned_json) as pairs(value, product_id)
                WHERE value != ''
            )
            SELECT 
                product_id,
                attr_name,
                attr_value
            FROM split_pairs
            WHERE attr_name != ''
                AND NOT attr_name LIKE 'style%'
        """)

        # Create indexes for better query performance
        conn.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_{table_name}_additional_attrs_name 
            ON {table_name}_additional_attrs (attr_name)
        """)
        conn.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_{table_name}_additional_attrs_value 
            ON {table_name}_additional_attrs (attr_value)
        """)

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
                        json_extract_string(extracted_product, 'materials') as materials,
                        json_extract_string(extracted_product, '$.audience.genders') as genders,
                        json_extract_string(extracted_product, '$.audience.age_groups') as age_groups,
                        json_extract_string(extracted_product, 'hasVariant') as variants_json,
                        json_extract_string(extracted_product, 'additional_attributes') as additional_attributes_json
                    FROM df
                    WHERE json_extract_string(extracted_product, 'productGroupID') IS NOT NULL
                """)

                # Count records before insertion
                pre_count = conn.execute(
                    f"SELECT COUNT(*) FROM {table_name}"
                ).fetchone()[0]

                # Insert non-duplicate records into both tables
                conn.execute(f"""
                    INSERT INTO {table_name}_extracted
                    SELECT t.* 
                    FROM temp_products t
                    WHERE NOT EXISTS (
                        SELECT 1 
                        FROM {table_name}_extracted m 
                        WHERE m.product_group_id = t.product_group_id
                    )
                """)

                conn.execute(f"""
                    INSERT INTO {table_name}
                    SELECT product_group_id, extracted_product
                    FROM temp_products t
                    WHERE NOT EXISTS (
                        SELECT 1 
                        FROM {table_name} m 
                        WHERE m.product_group_id = t.product_group_id
                    )
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


def load_parquet_files_to_db(
    download_path: str,
    catalog: str,
    db_type: str = "sqlite",
) -> None:
    """Load all parquet files from the download path into a SQLite or DuckDB database."""
    db_path = os.path.join(
        os.path.dirname(__file__), "..", f"{catalog}_catalog.{db_type}"
    )
    logger.info(f"Loading parquet files from {download_path} into {db_path}")

    # Connect to database based on type
    if db_type == "sqlite":
        conn = sqlite3.connect(db_path)
    else:  # duckdb
        conn = duckdb.connect(db_path, config={"allow_unsigned_extensions": "true"})

    table_name = os.path.splitext(catalog)[0].replace(os.sep, "_")
    parquet_files = glob.glob(
        os.path.join(download_path, "**/*.parquet"), recursive=True
    )

    try:
        # Read first file to determine if data is flattened
        if parquet_files:
            first_df = pd.read_parquet(parquet_files[0])
            is_flattened = is_data_flattened(first_df)
            logger.info(
                f"Detected {'flattened' if is_flattened else 'nested'} data format"
            )

        if db_type == "sqlite":
            total_products, duplicates_skipped = load_to_sqlite(
                conn, parquet_files, table_name, is_flattened
            )
        else:  # duckdb
            total_products, duplicates_skipped = load_to_duckdb(
                conn, parquet_files, table_name, is_flattened
            )

        logger.info(f"Finished loading all parquet files to {db_type} database.")
        logger.info(f"Total products loaded: {total_products}")
        logger.info(f"Duplicate products skipped: {duplicates_skipped}")
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Load Octogen catalog data to SQLite or DuckDB"
    )
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
    parser.add_argument(
        "--db-type",
        type=str,
        choices=["sqlite", "duckdb"],
        default="sqlite",
        help="Database type to use (sqlite or duckdb)",
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

    load_parquet_files_to_db(args.download, args.catalog, args.db_type)


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


# Add this function to pre-process additional attributes
def normalize_additional_attributes(product_data):
    """Extract and normalize additional attributes from product data."""
    try:
        additional_attrs = product_data.get("additional_attributes", {}) or {}
        if isinstance(additional_attrs, str):
            additional_attrs = json.loads(additional_attrs)

        # Filter out style-related attributes and normalize
        normalized_attrs = [
            {"attr_name": key, "attr_value": str(value)}
            for key, value in additional_attrs.items()
            if not key.startswith("style")
        ]
        return normalized_attrs
    except (json.JSONDecodeError, AttributeError):
        return []


# Modify the load_data function to create and populate the additional attributes table
def load_data(db_path: str, table_name: str, products: list):
    """Load product data into the database with a normalized additional attributes table."""
    is_duckdb = db_path.endswith(".duckdb")

    if is_duckdb:
        conn = duckdb.connect(db_path)
    else:
        conn = sqlite3.connect(db_path)

    cursor = conn.cursor()

    # Create the main products table
    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        product_id VARCHAR PRIMARY KEY,
        extracted_product TEXT,
        product_group_id VARCHAR,
        brand_name VARCHAR,
        name VARCHAR,
        description TEXT,
        price DECIMAL,
        original_price DECIMAL,
        rating DECIMAL,
        rating_count INTEGER,
        product_image VARCHAR,
        variants_json TEXT,
        materials TEXT,
        genders TEXT,
        age_groups TEXT,
        additional_attributes_json TEXT,
        updated_at TIMESTAMP
    )
    """
    cursor.execute(create_table_sql)

    # Create the normalized additional attributes table
    create_attrs_table_sql = f"""
    CREATE TABLE IF NOT EXISTS {table_name}_additional_attrs (
        product_id VARCHAR,
        attr_name VARCHAR,
        attr_value TEXT,
        PRIMARY KEY (product_id, attr_name)
    )
    """
    cursor.execute(create_attrs_table_sql)

    # Create indexes for better query performance
    cursor.execute(
        f"CREATE INDEX IF NOT EXISTS idx_{table_name}_attr_name ON {table_name}_additional_attrs(attr_name)"
    )
    cursor.execute(
        f"CREATE INDEX IF NOT EXISTS idx_{table_name}_attr_value ON {table_name}_additional_attrs(attr_value)"
    )

    # Begin transaction for faster inserts
    conn.execute("BEGIN TRANSACTION")

    try:
        for product in products:
            # Insert into main products table
            product_json = json.dumps(product)
            cursor.execute(
                f"""
                INSERT OR REPLACE INTO {table_name} (
                    product_id, extracted_product, product_group_id, brand_name,
                    name, description, price, original_price, rating,
                    rating_count, product_image, variants_json, materials,
                    genders, age_groups, additional_attributes_json, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    product.get("id"),
                    product_json,
                    product.get("product_group_id"),
                    product.get("brand_name"),
                    product.get("name"),
                    product.get("description"),
                    product.get("price"),
                    product.get("original_price"),
                    product.get("rating"),
                    product.get("rating_count"),
                    product.get("product_image"),
                    json.dumps(product.get("variants", [])),
                    json.dumps(product.get("materials", [])),
                    json.dumps(product.get("genders", [])),
                    json.dumps(product.get("age_groups", [])),
                    json.dumps(product.get("additional_attributes", {})),
                    product.get("updated_at"),
                ),
            )

            # Insert normalized additional attributes
            normalized_attrs = normalize_additional_attributes(product)
            for attr in normalized_attrs:
                cursor.execute(
                    f"""
                    INSERT OR REPLACE INTO {table_name}_additional_attrs 
                    (product_id, attr_name, attr_value) 
                    VALUES (?, ?, ?)
                    """,
                    (product.get("id"), attr["attr_name"], attr["attr_value"]),
                )

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


if __name__ == "__main__":
    main()
