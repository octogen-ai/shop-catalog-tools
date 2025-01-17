import argparse
import json
import os
import sys

import duckdb
from whoosh.analysis import StemmingAnalyzer
from whoosh.fields import DATETIME, ID, KEYWORD, NUMERIC, STORED, TEXT, Schema
from whoosh.index import create_in

# Add the src directory to the system path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from src.schema import AggregateOffer, Offer, Offers, ProductGroup

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
            rows = cursor.execute(
                f"SELECT extracted_product FROM {table_name} LIMIT {batch_size} OFFSET {offset}"
            ).fetchall()

            for row in rows:
                try:
                    # Parse JSON and create ProductGroup object
                    data = json.loads(row[0])
                    product = ProductGroup(**data)

                    # Handle offers in document creation
                    price = None
                    currency = None
                    offer_count = None
                    high_price = None
                    low_price = None
                    offer_urls = []
                    seller_names = []

                    try:
                        if product.offers:
                            if isinstance(product.offers, Offers):
                                # Handle list of individual offers
                                if product.offers.offers:
                                    valid_offers = [
                                        o
                                        for o in product.offers.offers
                                        if hasattr(o, "price") and o.price is not None
                                    ]
                                    offer_count = len(valid_offers)
                                    if valid_offers:
                                        prices = [o.price for o in valid_offers]
                                        if prices:
                                            high_price = max(prices)
                                            low_price = min(prices)
                                            price = (
                                                low_price  # Use lowest price as default
                                            )

                                        # Get currency from first valid offer with currency
                                        for offer in valid_offers:
                                            if (
                                                hasattr(offer, "priceCurrency")
                                                and offer.priceCurrency
                                            ):
                                                currency = offer.priceCurrency
                                                break

                                        # Collect seller names safely
                                        seller_names.extend(
                                            [
                                                o.seller.name
                                                for o in valid_offers
                                                if hasattr(o, "seller")
                                                and o.seller
                                                and hasattr(o.seller, "name")
                                                and o.seller.name
                                            ]
                                        )

                            elif isinstance(product.offers, AggregateOffer):
                                # Handle aggregate offer
                                if hasattr(product.offers, "offerCount"):
                                    offer_count = product.offers.offerCount
                                if hasattr(product.offers, "highPrice"):
                                    high_price = product.offers.highPrice
                                if hasattr(product.offers, "lowPrice"):
                                    low_price = product.offers.lowPrice
                                    price = low_price  # Use lowest price as default
                                if hasattr(product.offers, "priceCurrency"):
                                    currency = product.offers.priceCurrency
                                if (
                                    hasattr(product.offers, "seller")
                                    and product.offers.seller
                                    and hasattr(product.offers.seller, "name")
                                    and product.offers.seller.name
                                ):
                                    seller_names.append(product.offers.seller.name)

                            elif isinstance(product.offers, Offer):
                                # Handle single offer
                                offer_count = 1
                                if hasattr(product.offers, "price"):
                                    price = product.offers.price
                                    high_price = price
                                    low_price = price
                                if hasattr(product.offers, "priceCurrency"):
                                    currency = product.offers.priceCurrency
                                if (
                                    hasattr(product.offers, "seller")
                                    and product.offers.seller
                                    and hasattr(product.offers.seller, "name")
                                    and product.offers.seller.name
                                ):
                                    seller_names.append(product.offers.seller.name)

                        # Fallback to price_info if no offers price available
                        if price is None and product.price_info:
                            price = product.price_info.price
                            currency = product.price_info.currency_code

                    except Exception as e:
                        print(f"Error processing offers for product {product.id}: {e}")
                        # Continue with whatever price/currency info we managed to extract

                    # Add document to the index with proper field handling
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
                        "available_time": product.available_time,
                        "availability": product.availability,
                        "available_quantity": product.available_quantity,
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
                        "color_families": ",".join(
                            product.color_info.color_families or []
                        )
                        if product.color_info
                        else None,
                        "color_labels": ",".join(
                            color.label for color in (product.color_info.colors or [])
                        )
                        if product.color_info
                        else None,
                        "color_swatches": [
                            color.swatch_url
                            for color in (product.color_info.colors or [])
                            if color.swatch_url is not None
                        ]
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
    args = parser.parse_args()

    create_whoosh_index(
        args.db_path, args.index_dir, args.table_name, args.batch_size, args.db_type
    )


if __name__ == "__main__":
    main()
