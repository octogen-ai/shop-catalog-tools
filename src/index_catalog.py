import argparse
import json
import os
import sys
import uuid
from typing import Any, Dict, Optional, Union, get_args, get_origin

import duckdb
from pydantic import BaseModel
from whoosh.analysis import StemmingAnalyzer
from whoosh.fields import ID, KEYWORD, NUMERIC, STORED, TEXT, Schema
from whoosh.index import create_in

# Add the src directory to the system path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from octogen.api.types.category import Category
from octogen.api.types.color_info import Color, ColorInfo
from octogen.api.types.image import Image
from octogen.api.types.offer import Offer
from octogen.api.types.rating import Rating
from octogen.api.types.search_tool_output import Product

# Define analyzer for better text search
analyzer = StemmingAnalyzer()


# Dynamically build the schema based on the Product class
def build_schema_from_product_class():
    schema_fields = {}

    # Get all fields from the Product class
    product_fields = Product.model_fields

    # Map field types to Whoosh field types based on their annotations
    for field_name, field_info in product_fields.items():
        field_type = field_info.annotation

        # Get the docstring for this field if available
        docstring = field_info.description

        # Determine the appropriate Whoosh field type based on the field's annotation and name
        whoosh_field = determine_whoosh_field_type(field_name, field_type, docstring)

        if whoosh_field:
            schema_fields[field_name] = whoosh_field

    # Add derived fields from nested objects
    derived_fields = generate_derived_fields()
    schema_fields.update(derived_fields)
    print(f"Schema fields: {schema_fields.keys()}")
    return Schema(**schema_fields)


def determine_whoosh_field_type(
    field_name: str, field_type: Any, docstring: Optional[str] = None
) -> Any:
    """
    Determine the appropriate Whoosh field type based on the field's name, type annotation, and docstring.
    """
    # Special handling for the ID field which needs to be unique
    if field_name == "id":
        return ID(stored=True, unique=True)

    # Check if it's a string field
    if field_type in [str, Optional[str]]:
        # Identifier fields
        if field_name in ["uuid", "gtin", "product_group_id", "primary_product_id"]:
            return ID(stored=True)

        # URL field
        if field_name == "url":
            return ID(stored=True)

        # Text fields that should be analyzed for better search
        if field_name in ["name", "description", "extra_text"] or (
            docstring and "description" in docstring.lower()
        ):
            return TEXT(stored=True, analyzer=analyzer)

        # Default for other string fields
        return TEXT(stored=True)

    # Numeric fields
    if field_type in [float, int, Optional[float], Optional[int]]:
        return NUMERIC(stored=True)

    # Handle list types
    if get_origin(field_type) is list or (
        get_origin(field_type) is Union
        and any(get_origin(t) is list for t in get_args(field_type) if get_origin(t))
    ):
        # For lists of strings, use KEYWORD for better filtering
        if field_name in ["tags", "sizes", "materials", "patterns", "varies_by"]:
            return KEYWORD(stored=True, commas=True, lowercase=True)

        # For other lists, just store them
        return STORED

    # Handle Union types
    if get_origin(field_type) is Union:
        # If any of the Union types is a BaseModel, store as STORED
        if any(
            issubclass(t, BaseModel) if isinstance(t, type) else False
            for t in get_args(field_type)
            if t is not None
        ):
            return STORED

    # Handle complex types (Pydantic models)
    if isinstance(field_type, type) and issubclass(field_type, BaseModel):
        return STORED

    # Default to STORED for any other types
    return STORED


def generate_derived_fields() -> Dict[str, Any]:
    """
    Dynamically generate derived fields based on nested object types.
    """
    derived_fields = {}

    # Add derived fields from ColorInfo class
    color_info_fields = ColorInfo.model_fields
    if "color_families" in color_info_fields:
        derived_fields["color_families"] = KEYWORD(
            stored=True, commas=True, lowercase=True
        )

    # Add derived fields from Color class
    color_fields = Color.model_fields
    if "label" in color_fields:
        derived_fields["color_labels"] = KEYWORD(
            stored=True, commas=True, lowercase=True
        )
    if "swatch_url" in color_fields:
        derived_fields["color_swatches"] = STORED

    # Add derived fields from Rating class
    rating_fields = Rating.model_fields
    if "average_rating" in rating_fields:
        derived_fields["rating_value"] = NUMERIC(stored=True)
    if "rating_count" in rating_fields:
        derived_fields["review_count"] = NUMERIC(stored=True)

    # Add derived fields from Image class
    image_fields = Image.model_fields
    if "url" in image_fields:
        derived_fields["image_url"] = STORED
        derived_fields["image_urls"] = STORED

    # Add derived fields from Category class
    category_fields = Category.model_fields
    if "name" in category_fields:
        derived_fields["categories_text"] = KEYWORD(
            stored=True, commas=True, lowercase=True
        )

    # Add derived fields from Offer class
    offer_fields = Offer.model_fields
    derived_fields["offer_count"] = NUMERIC(stored=True)
    derived_fields["high_price"] = NUMERIC(stored=True)
    derived_fields["low_price"] = NUMERIC(stored=True)
    derived_fields["offer_urls"] = STORED
    derived_fields["seller_names"] = KEYWORD(stored=True, commas=True, lowercase=True)

    # Add brand_name field if not already in the Product class
    if (
        not hasattr(Product, "brand_name")
        or Product.model_fields.get("brand_name") is None
    ):
        derived_fields["brand_name"] = TEXT(stored=True)

    return derived_fields


# Create schema using the dynamic builder
schema = build_schema_from_product_class()


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
                    # Parse JSON and create product data
                    data = json.loads(row[0])

                    # Add a UUID if it's missing (required field)
                    if "uuid" not in data or not data["uuid"]:
                        # Generate a deterministic UUID based on the product ID or other unique fields
                        seed = data.get("id", "") or data.get("url", "") or str(data)
                        # Create a UUID v5 (namespace-based) using the seed
                        data["uuid"] = str(uuid.uuid5(uuid.NAMESPACE_DNS, seed))

                    # Create Product object with the updated data
                    product = Product(**data)

                    # Start with the product's model dump
                    doc = product.model_dump()

                    # Extract and add derived fields from nested objects
                    doc = extract_derived_fields(doc, product, row)

                    # Convert complex objects to strings for Whoosh indexing
                    doc = convert_complex_objects(doc)

                    # Add document to the index with proper field handling
                    writer.add_document(
                        **{
                            k: v
                            for k, v in doc.items()
                            if v is not None and k in schema.names()
                        }
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


def extract_derived_fields(
    doc: Dict[str, Any], product: Product, row: tuple
) -> Dict[str, Any]:
    """Extract derived fields from nested objects in the product."""
    # Initialize derived fields
    price = row[1] if row[1] is not None else product.current_price
    original_price = row[2] if row[2] is not None else product.original_price

    # Set price-related fields
    doc["current_price"] = price
    doc["original_price"] = original_price
    doc["high_price"] = original_price if original_price else price
    doc["low_price"] = price if price else original_price

    # Extract color information
    if product.color_info:
        # Extract color families
        if product.color_info.color_families:
            doc["color_families"] = ",".join(product.color_info.color_families)

        # Extract color labels and swatches
        if product.color_info.colors:
            color_labels = []
            color_swatches = []
            for color in product.color_info.colors:
                color_labels.append(color.label)
                if color.swatch_url:
                    color_swatches.append(color.swatch_url)

            if color_labels:
                doc["color_labels"] = ",".join(color_labels)
            if color_swatches:
                doc["color_swatches"] = color_swatches

    # Extract categories
    if product.categories:
        categories_text = [cat.name for cat in product.categories if cat.name]
        if categories_text:
            doc["categories_text"] = ",".join(categories_text)

    # Extract rating information
    if product.rating:
        doc["rating_value"] = product.rating.average_rating
        doc["review_count"] = product.rating.rating_count

    # Extract image information
    if product.image:
        doc["image_url"] = product.image.url

    if product.images:
        doc["image_urls"] = [img.url for img in product.images if img.url]

    # Handle fit field which can be a string or list
    if product.fit:
        if isinstance(product.fit, list):
            doc["fit"] = ",".join(product.fit)
        else:
            doc["fit"] = product.fit

    # Extract seller names from offers
    seller_names = []
    offer_urls = []
    offer_count = 0

    if product.offers:
        # Handle different offer types
        if hasattr(product.offers, "offers") and product.offers.offers:
            # This is a list of offers
            offers_list = product.offers.offers
            offer_count = len(offers_list)

            for offer in offers_list:
                if offer.seller and hasattr(offer.seller, "name") and offer.seller.name:
                    seller_names.append(offer.seller.name)
        elif hasattr(product.offers, "seller") and product.offers.seller:
            # This is a single offer with seller
            if hasattr(product.offers.seller, "name") and product.offers.seller.name:
                seller_names.append(product.offers.seller.name)
            offer_count = 1

    # Add offer information to doc
    if seller_names:
        doc["seller_names"] = ",".join(seller_names)
    if offer_urls:
        doc["offer_urls"] = offer_urls
    doc["offer_count"] = offer_count

    # Add brand_name if not already set
    if not doc.get("brand_name") and product.brand and hasattr(product.brand, "name"):
        doc["brand_name"] = product.brand.name

    return doc


def convert_complex_objects(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Convert complex objects to strings for Whoosh indexing."""
    for key, value in list(doc.items()):
        if isinstance(value, BaseModel):
            doc[key] = str(value)
        elif isinstance(value, list) and value and isinstance(value[0], BaseModel):
            doc[key] = str(value)
        elif isinstance(value, list) and value:
            # Convert lists to comma-separated strings for KEYWORD fields
            if key in schema.names() and isinstance(schema[key], KEYWORD):
                doc[key] = ",".join(str(v) for v in value)

    return doc


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
