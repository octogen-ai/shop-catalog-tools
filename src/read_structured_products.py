import sqlite3
import pandas as pd
from tabulate import tabulate
import argparse
import os
import sys
import os
import json

# Add the src directory to the system path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.schema import ProductGroup

def query_products_from_db(db_path: str, catalog: str, limit: int):
    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    
    # Determine the table name based on the catalog
    table_name = os.path.splitext(catalog)[0].replace(os.sep, "_")
    
    # Query products from the database with a limit
    query = f"SELECT * FROM {table_name} LIMIT {limit}"
    df = pd.read_sql_query(query, conn)
    
    # Close the connection
    conn.close()
    
    return df

def load_products_to_pydantic(df: pd.DataFrame):
    products = []
    for _, row in df.iterrows():
        # Deserialize the JSON from the 'extracted_product' column
        extracted_product_json = row['extracted_product']
        
        # Parse the JSON string into a dictionary
        extracted_product_data = json.loads(extracted_product_json)
        
        # Deserialize the dictionary into a ProductGroup object
        product = ProductGroup(**extracted_product_data)
        
        products.append(product)
        # print(product)
    return products

def print_products(products):
    # Convert products to a list of dictionaries for tabulation
    product_dicts = [product.model_dump() for product in products]
    
    # Remove the 'hasVariant' attribute from each product dictionary
    # Because it is massive, potentially.  
    for product_dict in product_dicts:
        product_dict.pop('hasVariant', None)
    
    # Create a DataFrame from the list of dictionaries
    df = pd.DataFrame(product_dicts)
    
    # Drop columns with all None/empty values
    df = df.dropna(axis=1, how='all')
    
    # Truncate each cell to the first 30 characters, add ellipsis and size
    size_limit = 20 # characters
    def format_cell(x):
        x_str = str(x)
        if len(x_str) > size_limit:
            return f"{x_str[:size_limit]}... ({len(x_str)})"
        return x_str
    
    df = df.map(format_cell)
    
    # Print the products in a tabular format
    print(tabulate(df.to_dict(orient='records'), headers="keys", tablefmt="grid"))

def main():
    parser = argparse.ArgumentParser(description="Query products from SQLite and print them.")
    parser.add_argument(
        "--db_path",
        type=str,
        help="Path to the SQLite database",
        required=True,
    )
    parser.add_argument(
        "--catalog",
        type=str,
        help="Name of the catalog",
        required=True,
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Number of products to query",
        default=100,
    )

    args = parser.parse_args()
    
    # Query products from the database
    df = query_products_from_db(args.db_path, args.catalog, args.limit)
    
    # Load products into Pydantic objects
    products = load_products_to_pydantic(df)
    
    # Print products
    print_products(products)

if __name__ == "__main__":
    main()
