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
from collections import Counter

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
    
    # Get total count of valid products (excluding null IDs)
    cursor.execute(f"""
        SELECT COUNT(*) FROM {table_name} 
        WHERE json_extract(extracted_product, '$.id') IS NOT NULL
    """)
    total_count = cursor.fetchone()[0]
    
    # Get paginated results, excluding products with null IDs
    cursor.execute(f"""
        SELECT extracted_product FROM {table_name}
        WHERE json_extract(extracted_product, '$.id') IS NOT NULL
        LIMIT ? OFFSET ?
    """, (per_page, (page - 1) * per_page))
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

@app.get("/api/{table_name}/analytics")
async def get_table_analytics(table_name: str):
    conn = get_db_connection(table_name)
    cursor = conn.cursor()
    
    # Get total number of records
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    total_records = cursor.fetchone()[0]
    
    # Analysis queries for common fields
    analytics = {
        "total_records": total_records,
        "null_analysis": {},
        "uniqueness_analysis": {},
        "value_distributions": {}
    }
    
    # Common fields to analyze
    fields_to_check = [
        "id", "name", "description", "brand_name", "price", 
        "currency", "availability", "url", "image_url"
    ]
    
    # Null analysis
    for field in fields_to_check:
        cursor.execute(f"""
            SELECT COUNT(*) 
            FROM {table_name} 
            WHERE json_extract(extracted_product, '$.{field}') IS NULL
        """)
        null_count = cursor.fetchone()[0]
        analytics["null_analysis"][field] = {
            "null_count": null_count,
            "null_percentage": round((null_count / total_records) * 100, 2)
        }
    
    # Uniqueness analysis
    for field in fields_to_check:
        cursor.execute(f"""
            SELECT COUNT(DISTINCT json_extract(extracted_product, '$.{field}'))
            FROM {table_name}
            WHERE json_extract(extracted_product, '$.{field}') IS NOT NULL
        """)
        unique_count = cursor.fetchone()[0]
        analytics["uniqueness_analysis"][field] = {
            "unique_values": unique_count,
            "uniqueness_percentage": round((unique_count / total_records) * 100, 2)
        }
    
    # Value distribution for categorical fields
    categorical_fields = ["brand_name", "availability", "currency"]
    for field in categorical_fields:
        cursor.execute(f"""
            SELECT json_extract(extracted_product, '$.{field}') as value, COUNT(*) as count
            FROM {table_name}
            WHERE json_extract(extracted_product, '$.{field}') IS NOT NULL
            GROUP BY json_extract(extracted_product, '$.{field}')
            ORDER BY count DESC
            LIMIT 10
        """)
        distribution = cursor.fetchall()
        analytics["value_distributions"][field] = [
            {"value": row[0], "count": row[1]} 
            for row in distribution
        ]
    
    conn.close()
    return JSONResponse(analytics)

@app.get("/api/{table_name}/advanced-analytics")
async def get_advanced_analytics(table_name: str):
    conn = get_db_connection(table_name)
    
    # Check if connection is DuckDB
    if not isinstance(conn, duckdb.DuckDBPyConnection):
        raise HTTPException(
            status_code=400, 
            detail="Advanced analytics are only available with DuckDB database engine"
        )
    
    cursor = conn.cursor()
    analytics = {
        "variant_analysis": {},
        "price_distribution": {},
        "size_availability": {},
        "color_combinations": {}
    }
    
    # 1. Variant Analysis - Count of variants per product and distribution
    cursor.execute(f"""
        SELECT 
            json_array_length(json_extract(extracted_product, '$.hasVariant')) as variant_count,
            COUNT(*) as product_count,
            (COUNT(*) * 100.0 / (SELECT COUNT(*) FROM {table_name})) as percentage
        FROM {table_name}
        WHERE json_extract(extracted_product, '$.hasVariant') IS NOT NULL
        GROUP BY variant_count
        ORDER BY variant_count
    """)
    analytics["variant_analysis"]["distribution"] = [
        {"variant_count": row[0], "product_count": row[1], "percentage": round(row[2], 2)}
        for row in cursor.fetchall()
    ]
    
    # 2. Price Distribution with Statistical Analysis
    cursor.execute(f"""
        WITH price_data AS (
            SELECT 
                json_extract(extracted_product, '$.price_info.price')::FLOAT as price
            FROM {table_name}
            WHERE json_extract(extracted_product, '$.price_info.price') IS NOT NULL
        )
        SELECT 
            MIN(price) as min_price,
            MAX(price) as max_price,
            AVG(price) as avg_price,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price) as median_price,
            STDDEV(price) as std_dev,
            PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY price) as q1,
            PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY price) as q3
        FROM price_data
    """)
    row = cursor.fetchone()
    analytics["price_distribution"]["statistics"] = {
        "min_price": round(row[0], 2),
        "max_price": round(row[1], 2),
        "avg_price": round(row[2], 2),
        "median_price": round(row[3], 2),
        "std_dev": round(row[4], 2),
        "q1": round(row[5], 2),
        "q3": round(row[6], 2)
    }
    
    # 3. Size Availability Analysis
    cursor.execute(f"""
        WITH RECURSIVE size_data AS (
            SELECT 
                unnest(json_extract(extracted_product, '$.sizes')::JSON[]) as size,
                json_extract(extracted_product, '$.availability')::VARCHAR as availability
            FROM {table_name}
            WHERE json_extract(extracted_product, '$.sizes') IS NOT NULL
        )
        SELECT 
            size,
            COUNT(*) as total_count,
            SUM(CASE WHEN availability = 'IN_STOCK' THEN 1 ELSE 0 END) as in_stock_count,
            SUM(CASE WHEN availability = 'OUT_OF_STOCK' THEN 1 ELSE 0 END) as out_of_stock_count
        FROM size_data
        GROUP BY size
        ORDER BY total_count DESC
        LIMIT 20
    """)
    analytics["size_availability"]["distribution"] = [
        {
            "size": row[0],
            "total_count": row[1],
            "in_stock_count": row[2],
            "out_of_stock_count": row[3]
        }
        for row in cursor.fetchall()
    ]
    
    # 4. Color Combinations Analysis
    cursor.execute(f"""
        WITH RECURSIVE color_data AS (
            SELECT 
                unnest(json_extract(extracted_product, '$.color_info.colors')::JSON[]) as color,
                json_extract(extracted_product, '$.color_info.color_families')::JSON[] as families
            FROM {table_name}
            WHERE json_extract(extracted_product, '$.color_info.colors') IS NOT NULL
        )
        SELECT 
            color,
            array_to_string(families, ', ') as color_families,
            COUNT(*) as frequency
        FROM color_data
        GROUP BY color, families
        ORDER BY frequency DESC
        LIMIT 20
    """)
    analytics["color_combinations"]["popular_combinations"] = [
        {
            "color": row[0],
            "color_families": row[1],
            "frequency": row[2]
        }
        for row in cursor.fetchall()
    ]
    
    conn.close()
    return JSONResponse(analytics)