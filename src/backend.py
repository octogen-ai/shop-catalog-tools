from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse, Response
from dotenv import load_dotenv
import json
import sqlite3
import os
from whoosh.index import open_dir
from whoosh.qparser import QueryParser, MultifieldParser
import math
import yaml
from fastapi.templating import Jinja2Templates
from pathlib import Path
import duckdb
from typing import Union

app = FastAPI()

# Serve the Svelte app
app.mount("/static", StaticFiles(directory="src/app/dist", html=True), name="app")

# Database connection
def get_db_connection(table_name: str) -> Union[sqlite3.Connection, duckdb.DuckDBPyConnection]:
    load_dotenv()
    db_engine = os.getenv('DB_ENGINE', 'sqlite').lower()
    
    if db_engine == 'duckdb':
        db_path = os.path.join(os.path.dirname(__file__), "..", f"{table_name}_catalog.duckdb")
        if not os.path.exists(db_path):
            raise HTTPException(status_code=404, detail=f"Database {table_name}_catalog.duckdb not found")
        return duckdb.connect(db_path)
    else:  # sqlite. Can either be .db or .sqlite (to be backkwards compatible.)
        db_path = os.path.join(os.path.dirname(__file__), "..", f"{table_name}_catalog.db")
        if not os.path.exists(db_path):
            db_path = os.path.join(os.path.dirname(__file__), "..", f"{table_name}_catalog.sqlite")
        if not os.path.exists(db_path):
            raise HTTPException(status_code=404, detail=f"Database {table_name}_catalog.db not found")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn

# Add to imports at top
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

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
    
    # Get paginated results
    cursor.execute(
        f"SELECT extracted_product FROM {table_name} LIMIT ? OFFSET ?", 
        (per_page, (page - 1) * per_page)
    )
    products = cursor.fetchall()
    conn.close()
    
    return JSONResponse({
        "products": [json.loads(row[0] if isinstance(conn, duckdb.DuckDBPyConnection) else row['extracted_product']) for row in products],
        "total": total_count,
        "page": page,
        "per_page": per_page,
        "total_pages": math.ceil(total_count / per_page)
    })

@app.get("/api/{table_name}/search")
async def search_products(table_name: str, query: str, page: int = 1, per_page: int = 12):
    # Open Whoosh index
    index_dir = f"/tmp/whoosh/{table_name}"
    if not os.path.exists(index_dir):
        raise HTTPException(status_code=404, detail=f"Search index not found for {table_name}")
    
    ix = open_dir(index_dir)
    
    # Search across all relevant text fields
    searchable_fields = [
        "name",
        "description",
        "brand_name",
        "extra_text",
        "tags",
        "categories",
        "materials",
        "patterns",
        "colors",
        "sizes"
    ]
    
    parser = MultifieldParser(searchable_fields, schema=ix.schema)
    parsed_query = parser.parse(query)
    
    with ix.searcher() as searcher:
        # Use search_page for pagination
        results = searcher.search_page(parsed_query, page, pagelen=per_page)
        total_count = results.total
        product_ids = [result['id'] for result in results]
        print(f"Found {total_count} total products, returning page {page} for query: {query}")
    
    if not product_ids:
        return JSONResponse({
            "products": [],
            "total": 0,
            "page": page,
            "per_page": per_page,
            "total_pages": 0
        })

    # Get full product data from SQLite
    conn = get_db_connection(table_name)
    placeholders = ','.join(['?' for _ in product_ids])
    
    cursor = conn.cursor()
    products = cursor.execute(
        f"SELECT extracted_product FROM {table_name} WHERE json_extract(extracted_product, '$.id') IN ({placeholders})",
        product_ids
    ).fetchall()
        
    conn.close()

    return JSONResponse({
        "products": [json.loads(row[0] if isinstance(conn, duckdb.DuckDBPyConnection) else row['extracted_product']) for row in products],
        "total": total_count,
        "page": page,
        "per_page": per_page,
        "total_pages": math.ceil(total_count / per_page)
    })

def format_yaml_as_html(yaml_str: str) -> str:
    lines = yaml_str.split('\n')
    processed_lines = []
    
    for line in lines:
        if ':' in line:
            # Split on first colon and handle attribute names
            attr_name, value = line.split(':', 1)
            if 'url' in attr_name:
                # Handle URL values specially
                url = value.strip()
                processed_lines.append(f'<strong>{attr_name}</strong>: <a href="{url}">{url}</a>')
            else:
                # Make regular attributes bold
                processed_lines.append(f'<strong>{attr_name}</strong>:{value}')
        else:
            processed_lines.append(line)
    
    return '<pre>' + '\n'.join(processed_lines) + '</pre>'

@app.get("/api/{table}/product/{product_id}/raw")
async def get_raw_product(
    request: Request,
    table: str, 
    product_id: str, 
    format: str = "json"
):
    conn = get_db_connection(table)
    cursor = conn.cursor()
    
    cursor.execute(
        f"SELECT extracted_product FROM {table} WHERE product_group_id = ?",
        (product_id,)
    )
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        raise HTTPException(status_code=404, detail="Product not found")
    
    data = json.loads(result[0])
    formats = {
        'json': 'JSON',
        'yaml': 'YAML',
        'tree': 'Tree View'
    }
    
    template_context = {
        "request": request,
        "formats": formats,
        "current_format": format.lower(),
        "format": format.lower(),
        "json_data": json.dumps(data)
    }
    
    if format.lower() == "yaml":
        yaml_str = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
        template_context["content"] = format_yaml_as_html(yaml_str)
    elif format.lower() == "json":
        template_context["content"] = json.dumps(data, indent=2)
    
    return templates.TemplateResponse(
        "product_view.html",
        template_context
    )