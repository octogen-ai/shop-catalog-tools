import argparse
import json
import os
import sqlite3
import sys

import duckdb
from whoosh.analysis import StemmingAnalyzer
from whoosh.fields import DATETIME, ID, KEYWORD, NUMERIC, STORED, TEXT, Schema
from whoosh.index import create_in

# Add the src directory to the system path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from src.schema import ProductGroup

# Define analyzer for better text search
analyzer = StemmingAnalyzer()

# Define the Whoosh schema based on ProductGroup fields
schema = Schema(
    id=ID(stored=True, unique=True),
    name=TEXT(stored=True, analyzer=analyzer),
    description=TEXT(stored=True, analyzer=analyzer),
    productGroupID=ID(stored=True),
    variesBy=KEYWORD(stored=True, commas=True, lowercase=True),
    catalog=TEXT(stored=True),
    url=ID(stored=True),
    primary_product_id=ID(stored=True),
    gtin=TEXT(stored=True),
    language_code=TEXT(stored=True),
    tags=KEYWORD(stored=True, commas=True, lowercase=True),
    available_time=DATETIME(stored=True),
    availability=TEXT(stored=True),
    available_quantity=NUMERIC(stored=True),
    sizes=KEYWORD(stored=True, commas=True, lowercase=True),
    materials=KEYWORD(stored=True, commas=True, lowercase=True),
    patterns=KEYWORD(stored=True, commas=True, lowercase=True),
    extra_text=TEXT(stored=True, analyzer=analyzer),
    brand_name=TEXT(stored=True),
    price=NUMERIC(stored=True),
    currency=STORED,
    color_families=KEYWORD(stored=True, commas=True, lowercase=True),
    colors=KEYWORD(stored=True, commas=True, lowercase=True),
    categories=KEYWORD(stored=True, commas=True, lowercase=True),
    rating=NUMERIC(stored=True),
    review_count=NUMERIC(stored=True),
    image_url=STORED,
    image_urls=STORED,
)


def create_whoosh_index(
    db_path: str,
    index_dir: str,
    table_name: str,
    batch_size: int = 1000,
    db_type: str = "sqlite",
):
    """Create a Whoosh index from SQLite/DuckDB database contents"""
    if not index_dir:
        index_dir = f"/tmp/whoosh/{table_name}"
    if not db_path:
        db_path = f"{table_name}_catalog.{db_type}"
    if not os.path.exists(db_path):
        print(f"Database file {db_path} does not exist")
        return

    # Connect to the database based on type
    if db_type == "sqlite":
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
    else:  # duckdb
        conn = duckdb.connect(db_path)
        cursor = conn

    # Create the index directory if it doesn't exist
    if not os.path.exists(index_dir):
        os.makedirs(index_dir)

    # Create a Whoosh index
    ix = create_in(index_dir, schema)
    writer = ix.writer()

    try:
        # Get total count of rows
        if db_type == "sqlite":
            cursor.execute(
                f"SELECT COUNT(*) FROM {table_name} WHERE json_extract(extracted_product, '$.productGroupID') IS NOT NULL"
            )
            total_rows = cursor.fetchone()[0]
        else:  # duckdb
            total_rows = cursor.execute(
                f"SELECT COUNT(*) FROM {table_name} WHERE json_extract_string(extracted_product, '$.productGroupID') IS NOT NULL"
            ).fetchone()[0]

        print(f"Found {total_rows} products to index")

        # Process in batches
        for offset in range(0, total_rows, batch_size):
            if db_type == "sqlite":
                cursor.execute(
                    f"SELECT extracted_product FROM {table_name} WHERE json_extract(extracted_product, '$.productGroupID') IS NOT NULL LIMIT ? OFFSET ?",
                    (batch_size, offset),
                )
                rows = cursor.fetchall()
            else:  # duckdb
                rows = cursor.execute(
                    f"SELECT extracted_product FROM {table_name} WHERE json_extract_string(extracted_product, '$.productGroupID') IS NOT NULL LIMIT {batch_size} OFFSET {offset}"
                ).fetchall()

            for row in rows:
                try:
                    # Parse JSON and create ProductGroup object
                    data = json.loads(row[0])
                    product = ProductGroup(**data)

                    # Add document to the index with proper field handling
                    doc = {
                        "id": product.productGroupID,
                        "name": product.name,
                        "description": product.description,
                        "productGroupID": product.productGroupID,
                        "variesBy": ",".join(product.variesBy or []),
                        "catalog": product.catalog,
                        "url": product.url,
                        "primary_product_id": product.primary_product_id,
                        "gtin": product.gtin,
                        "language_code": product.language_code,
                        "tags": ",".join(product.tags or []),
                        "available_time": product.available_time,
                        "availability": product.availability,
                        "available_quantity": product.available_quantity,
                        "sizes": ",".join(product.sizes or []),
                        "materials": ",".join(product.materials or []),
                        "patterns": ",".join(product.patterns or []),
                        "extra_text": product.extra_text,
                        "brand_name": product.brand.name if product.brand else None,
                        "price": product.price_info.price
                        if product.price_info
                        else None,
                        "currency": product.price_info.currency_code
                        if product.price_info
                        else None,
                        "color_families": ",".join(
                            product.color_info.color_families or []
                        )
                        if product.color_info
                        else None,
                        "colors": ",".join(product.color_info.colors or [])
                        if product.color_info
                        else None,
                        "categories": ",".join(
                            cat.name for cat in (product.categories or [])
                        ),
                        "rating": product.rating.average_rating
                        if product.rating
                        else None,
                        "review_count": product.rating.rating_count
                        if product.rating
                        else None,
                        "image_url": product.image.url if product.image else None,
                        "image_urls": [img.url for img in product.images]
                        if product.images
                        else None,
                    }
                    writer.add_document(
                        **{k: v for k, v in doc.items() if v is not None}
                    )

                except Exception as e:
                    print(f"Error processing product: {e}")
                    continue

            print(
                f"Indexed {min(offset + batch_size, total_rows)} of {total_rows} products"
            )

        writer.commit()
        print("Indexing completed successfully")

    except Exception as e:
        print(f"Error during indexing: {e}")
        writer.cancel()
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Index products using Whoosh")
    parser.add_argument("--db_path", type=str, help="Path to the database")
    parser.add_argument(
        "--index_dir", type=str, help="Directory to store the Whoosh index"
    )
    parser.add_argument(
        "--table_name", type=str, help="Name of the table to index", required=True
    )
    parser.add_argument(
        "--batch_size", type=int, help="Batch size for indexing", default=1000
    )
    parser.add_argument(
        "--db-type",
        type=str,
        choices=["sqlite", "duckdb"],
        default="sqlite",
        help="Database type to use (sqlite or duckdb)",
    )

    args = parser.parse_args()

    create_whoosh_index(
        args.db_path, args.index_dir, args.table_name, args.batch_size, args.db_type
    )


if __name__ == "__main__":
    main()
