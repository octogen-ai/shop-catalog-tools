import argparse
import json
import os
import sys

import duckdb
from whoosh.analysis import StemmingAnalyzer
from whoosh.fields import ID, KEYWORD, NUMERIC, STORED, TEXT, Schema
from whoosh.index import create_in

# Add the src directory to the system path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from src.schema import (
    ProductGroup,
)

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
    sizes=KEYWORD(stored=True, commas=True, lowercase=True),
    materials=KEYWORD(stored=True, commas=True, lowercase=True),
    patterns=KEYWORD(stored=True, commas=True, lowercase=True),
    extra_text=TEXT(stored=True, analyzer=analyzer),
    brand_name=TEXT(stored=True),
    price=NUMERIC(stored=True),
    currency=STORED,
    color_families=KEYWORD(stored=True, commas=True, lowercase=True),
    color_labels=KEYWORD(stored=True, commas=True, lowercase=True),
    color_swatches=STORED,
    categories=KEYWORD(stored=True, commas=True, lowercase=True),
    rating=NUMERIC(stored=True),
    review_count=NUMERIC(stored=True),
    image_url=STORED,
    image_urls=STORED,
    offer_count=NUMERIC(stored=True),
    high_price=NUMERIC(stored=True),
    low_price=NUMERIC(stored=True),
    offer_urls=STORED,
    seller_names=KEYWORD(stored=True, commas=True, lowercase=True),
)


def create_whoosh_index(
    db_path: str, index_dir: str, table_name: str, batch_size: int = 1000
):
    """Create a Whoosh index from DuckDB database contents"""
    if not index_dir:
        index_dir = f"/tmp/whoosh/{table_name}"
    if not db_path:
        db_path = f"{table_name}_catalog.duckdb"
    if not os.path.exists(db_path):
        print(f"Database file {db_path} does not exist")
        return

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
        total_rows = cursor.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]

        print(f"Found {total_rows} products to index")

        # Process in batches
        for offset in range(0, total_rows, batch_size):
            # Modified query to use extracted table with pre-extracted price fields
            rows = cursor.execute(f"""
                SELECT e.extracted_product, e.price, e.original_price 
                FROM {table_name}_extracted e 
                LIMIT {batch_size} OFFSET {offset}
            """).fetchall()

            for row in rows:
                try:
                    # Parse JSON and create ProductGroup object
                    data = json.loads(row[0])
                    product = ProductGroup(**data)

                    # Initialize fields
                    price = row[1]  # Use pre-extracted price
                    original_price = row[2]  # Use pre-extracted original price
                    currency = None
                    offer_count = None
                    high_price = original_price if original_price else price
                    low_price = price if price else original_price
                    offer_urls = []
                    seller_names = []
                    color_families = []
                    color_labels = []
                    color_swatches = []
                    categories = []
                    rating_value = None
                    review_count = None
                    image_url = None
                    image_urls = []

                    # Handle color_info
                    if product.color_info:
                        if product.color_info.color_families:
                            color_families.extend(product.color_info.color_families)
                        if product.color_info.colors:
                            for color in product.color_info.colors:
                                color_labels.append(color.label)
                                if color.swatch_url:
                                    color_swatches.append(color.swatch_url)

                    # Handle categories
                    if product.categories:
                        categories = [
                            cat.name for cat in product.categories if cat.name
                        ]

                    # Handle rating
                    if product.rating:
                        rating_value = product.rating.average_rating
                        review_count = product.rating.rating_count

                    # Handle images
                    if product.image:
                        image_url = product.image.url
                    if product.images:
                        image_urls = [img.url for img in product.images if img.url]

                    # Prepare document fields
                    doc = {
                        "id": product.id,
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
                        "sizes": ",".join(product.sizes or []),
                        "materials": ",".join(product.materials or []),
                        "patterns": ",".join(product.patterns or []),
                        "extra_text": product.extra_text,
                        "brand_name": product.brand.name if product.brand else None,
                        "price": price,
                        "currency": currency,
                        "offer_count": offer_count,
                        "high_price": high_price,
                        "low_price": low_price,
                        "offer_urls": offer_urls,
                        "seller_names": ",".join(seller_names)
                        if seller_names
                        else None,
                        "color_families": ",".join(color_families),
                        "color_labels": ",".join(color_labels),
                        "color_swatches": color_swatches,
                        "categories": ",".join(categories),
                        "rating": rating_value,
                        "review_count": review_count,
                        "image_url": image_url,
                        "image_urls": image_urls,
                    }

                    # Add document to the index with proper field handling
                    writer.add_document(
                        **{k: v for k, v in doc.items() if v is not None}
                    )

                except Exception as e:
                    print(f"Error processing product: {e}")
                    continue

            print(
                f"Indexed {min(offset + batch_size, total_rows)} of {total_rows} products into {index_dir}"
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
    args = parser.parse_args()

    create_whoosh_index(args.db_path, args.index_dir, args.table_name, args.batch_size)


if __name__ == "__main__":
    main()
