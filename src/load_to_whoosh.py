import os
import sqlite3
import json
import argparse
from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, TEXT, ID, KEYWORD, NUMERIC, DATETIME
from whoosh.qparser import QueryParser

import sys
import os

# Add the src directory to the system path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.schema import ProductGroup

# Define the Whoosh schema based on ProductGroup fields
schema = Schema(
    id=ID(stored=True, unique=True),
    name=TEXT(stored=True),
    description=TEXT(stored=True),
    productGroupID=ID(stored=True),
    variesBy=KEYWORD(stored=True, commas=True),
    catalog=TEXT(stored=True),
    url=ID(stored=True),
    primary_product_id=ID(stored=True),
    gtin=TEXT(stored=True),
    language_code=TEXT(stored=True),
    tags=KEYWORD(stored=True, commas=True),
    available_time=DATETIME(stored=True),
    availability=TEXT(stored=True),
    available_quantity=NUMERIC(stored=True),
    sizes=KEYWORD(stored=True, commas=True),
    materials=KEYWORD(stored=True, commas=True),
    patterns=KEYWORD(stored=True, commas=True),
    extra_text=TEXT(stored=True),
    image=TEXT(stored=True),  # Assuming image URL is stored as text
    images=KEYWORD(stored=True, commas=True),  # Assuming multiple image URLs
    reviews=KEYWORD(stored=True, commas=True),  # Assuming reviews are stored as text
    rating=NUMERIC(stored=True),  # Assuming rating is a numeric value
    # Add other fields as necessary
)

def create_whoosh_index(db_path: str, index_dir: str, table_name: str):
    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create the index directory if it doesn't exist
    if not os.path.exists(index_dir):
        os.mkdir(index_dir)

    # Create a Whoosh index
    ix = create_in(index_dir, schema)

    # Start indexing
    writer = ix.writer()

    # Query all rows from the table
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()

    # Get the index of the 'extracted_product' column
    column_names = [description[0] for description in cursor.description]
    extracted_product_index = column_names.index('extracted_product')

    for row in rows:
        # Deserialize JSON data from the 'extracted_product' column
        extracted_product_json = row[extracted_product_index]
        data = json.loads(extracted_product_json)
        product_group = ProductGroup(**data)

        # Add document to the index
        writer.add_document(
            id=product_group.id,
            name=product_group.name,
            description=product_group.description,
            productGroupID=product_group.productGroupID,
            variesBy=",".join(product_group.variesBy or []),
            catalog=product_group.catalog,
            url=product_group.url,
            primary_product_id=product_group.primary_product_id,
            gtin=product_group.gtin,
            language_code=product_group.language_code,
            tags=",".join(product_group.tags or []),
            available_time=product_group.available_time,
            availability=product_group.availability,
            available_quantity=product_group.available_quantity,
            sizes=",".join(product_group.sizes or []),
            materials=",".join(product_group.materials or []),
            patterns=",".join(product_group.patterns or []),
            extra_text=product_group.extra_text,
            image=product_group.image.url if product_group.image else None,
            images=",".join(img.url for img in product_group.images or []),
            reviews=",".join(str(review) for review in product_group.review or []),
            rating=product_group.rating.average_rating if product_group.rating else None,
            # Add other fields as necessary
        )

    writer.commit()
    conn.close()

def search_index(index_dir: str, query_str: str):
    # Open the index
    ix = open_dir(index_dir)

    # Create a query parser
    parser = QueryParser("description", schema=ix.schema)

    # Parse the query
    query = parser.parse(query_str)

    # Search the index
    with ix.searcher() as searcher:
        results = searcher.search(query)
        for result in results:
            print(dict(result))

def main():
    parser = argparse.ArgumentParser(description="Index and search products using Whoosh")
    parser.add_argument("--db_path", type=str, help="Path to the SQLite database", required=True)
    parser.add_argument("--index_dir", type=str, help="Directory to store the Whoosh index", required=True)
    parser.add_argument("--table_name", type=str, help="Name of the table to index", required=True)
    parser.add_argument("--query", type=str, help="Search query", required=False)

    args = parser.parse_args()

    create_whoosh_index(args.db_path, args.index_dir, args.table_name)

    if args.query:
        search_index(args.index_dir, args.query)

if __name__ == "__main__":
    main()