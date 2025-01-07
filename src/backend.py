from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
import json
import sqlite3
import os
from whoosh.index import open_dir
from whoosh.qparser import QueryParser
import math

app = FastAPI()

# Serve the Svelte app
app.mount("/static", StaticFiles(directory="src/app/dist", html=True), name="app")

# Database connection
def get_db_connection(table_name: str):
    db_path = os.path.join(os.path.dirname(__file__), "..", f"{table_name}_catalog.db")
    if not os.path.exists(db_path):
        raise HTTPException(status_code=404, detail=f"Database {table_name}_catalog.db not found")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/")
async def root():
    return FileResponse("src/app/dist/index.html")

@app.get("/api/{table_name}/products")
async def get_products(table_name: str, page: int = 1, per_page: int = 12):
    conn = get_db_connection(table_name)
    cursor = conn.cursor()
    
    # Get total count
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    total_count = cursor.fetchone()[0]
    
    # Calculate offset
    offset = (page - 1) * per_page
    
    # Get paginated results
    cursor.execute(
        f"SELECT extracted_product FROM {table_name} LIMIT ? OFFSET ?", 
        (per_page, offset)
    )
    products = cursor.fetchall()
    conn.close()
    
    return JSONResponse({
        "products": [json.loads(row['extracted_product']) for row in products],
        "total": total_count,
        "page": page,
        "per_page": per_page,
        "total_pages": math.ceil(total_count / per_page)
    })

@app.get("/api/{table_name}/search")
async def search_products(table_name: str, query: str):
    # Open Whoosh index
    index_dir = f"/tmp/whoosh/{table_name}"
    if not os.path.exists(index_dir):
        raise HTTPException(status_code=404, detail=f"Search index not found for {table_name}")
    
    ix = open_dir(index_dir)
    parser = QueryParser("description", schema=ix.schema)
    parsed_query = parser.parse(query)

    with ix.searcher() as searcher:
        results = searcher.search(parsed_query)
        product_ids = [result['id'] for result in results]

    if not product_ids:
        return JSONResponse({
            "products": [],
            "total": 0
        })

    # Get full product data from SQLite
    conn = get_db_connection(table_name)
    cursor = conn.cursor()
    
    placeholders = ','.join(['?' for _ in product_ids])
    
    cursor.execute(
        f"SELECT extracted_product FROM {table_name} WHERE json_extract(extracted_product, '$.id') IN ({placeholders})",
        product_ids
    )
    products = cursor.fetchall()
    conn.close()

    return JSONResponse({
        "products": [json.loads(row['extracted_product']) for row in products],
        "total": len(products)
    })