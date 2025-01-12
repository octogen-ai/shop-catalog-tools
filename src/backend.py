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
    total_records = cursor.fetchone()[0] or 0  # Default to 0 if None
    
    # Analysis queries for common fields
    analytics = {
        "total_records": total_records,
        "null_analysis": {},
        "uniqueness_analysis": {},
        "value_distributions": {}
    }
    
    # Common fields to analyze based on schema
    fields_to_check = [
        # Basic product info
        'id', 'catalog', 'url', 'name', 'type', 'primary_product_id', 'description', 'gtin',
        
        # Price and availability
        'price_info.price', 'price_info.original_price', 'price_info.currency_code', 'availability',
        'available_quantity',
        
        # Product details
        'brand.name', 'language_code', 'color_info.colors', 'sizes', 'materials', 'fit', 
        'dimensions', 'patterns',
        
        # Media
        'image.url', 'images', 'three_d_model',
        
        # Ratings and reviews
        'rating.average_rating', 'rating.rating_count', 'review',
        
        # Variant info
        'productGroupID', 'variesBy', 'hasVariant',
        
        # Additional info
        'additional_attributes', 'tags', 'promotions', 'audience', 'fulfillment_info'
    ]

    # Modify the null analysis query to handle nested fields
    for field in fields_to_check:
        json_path = field.replace('.', '->')  # Use -> for JSON path in DuckDB
        try:
            cursor.execute(f"""
                SELECT COUNT(*) 
                FROM {table_name} 
                WHERE json_extract(extracted_product, '{json_path}') IS NULL
            """)
            null_count = cursor.fetchone()[0] or 0  # Default to 0 if None
            analytics["null_analysis"][field] = {
                "null_count": null_count,
                "null_percentage": round((null_count / total_records) * 100, 2) if total_records > 0 else 0
            }
        except Exception as e:
            analytics["null_analysis"][field] = {
                "null_count": 0,
                "null_percentage": 0
            }

    # Modify the uniqueness analysis to handle nested fields
    for field in fields_to_check:
        json_path = field.replace('.', '->')  # Use -> for JSON path in DuckDB
        try:
            cursor.execute(f"""
                SELECT COUNT(DISTINCT json_extract(extracted_product, '{json_path}'))
                FROM {table_name}
                WHERE json_extract(extracted_product, '{json_path}') IS NOT NULL
            """)
            unique_count = cursor.fetchone()[0] or 0  # Default to 0 if None
            analytics["uniqueness_analysis"][field] = {
                "unique_values": unique_count,
                "uniqueness_percentage": round((unique_count / total_records) * 100, 2) if total_records > 0 else 0
            }
        except Exception as e:
            analytics["uniqueness_analysis"][field] = {
                "unique_values": 0,
                "uniqueness_percentage": 0
            }

    # Modify categorical fields analysis
    categorical_fields = [
        'brand.name', 'availability', 'price_info.currency_code', 
        'language_code', 'color_info.colors', 'materials', 'patterns',
        'type', 'audience'
    ]

    for field in categorical_fields:
        json_path = field.replace('.', '->')  # Use -> for JSON path in DuckDB
        try:
            cursor.execute(f"""
                SELECT 
                    COALESCE(json_extract(extracted_product, '{json_path}'), 'null') as value,
                    COUNT(*) as count
                FROM {table_name}
                WHERE json_extract(extracted_product, '{json_path}') IS NOT NULL
                GROUP BY json_extract(extracted_product, '{json_path}')
                ORDER BY count DESC
                LIMIT 10
            """)
            distribution = cursor.fetchall()
            analytics["value_distributions"][field] = [
                {"value": str(row[0]) if row[0] is not None else "null", "count": row[1] or 0} 
                for row in distribution
            ] if distribution else []
        except Exception as e:
            analytics["value_distributions"][field] = []

    conn.close()
    return JSONResponse(analytics)

@app.get("/api/{table_name}/advanced-analytics")
async def get_advanced_analytics(table_name: str):
    conn = get_db_connection(table_name)
    
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
        "color_combinations": {},
        "discount_analysis": {},
        "rating_analysis": {},
        "material_analysis": {},
        "brand_analysis": {},
        "audience_analysis": {},
        "availability_analysis": {}
    }

    # 1. Discount Analysis
    cursor.execute(f"""
        WITH discount_data AS (
            SELECT 
                CASE 
                    WHEN json_extract_string(extracted_product, '$.price_info.original_price') IS NULL THEN 0
                    ELSE ((CAST(json_extract_string(extracted_product, '$.price_info.original_price') AS FLOAT) - 
                           CAST(json_extract_string(extracted_product, '$.price_info.price') AS FLOAT)) / 
                           CAST(json_extract_string(extracted_product, '$.price_info.original_price') AS FLOAT) * 100)
                END as discount_percentage,
                CAST(json_extract_string(extracted_product, '$.rating.average_rating') AS FLOAT) as rating
            FROM {table_name}
            WHERE json_extract_string(extracted_product, '$.price_info.price') IS NOT NULL
        )
        SELECT 
            CASE 
                WHEN discount_percentage = 0 THEN 'No Discount'
                WHEN discount_percentage < 25 THEN '1-25%'
                WHEN discount_percentage < 50 THEN '26-50%'
                ELSE '50%+'
            END as discount_range,
            COUNT(*) as product_count,
            AVG(rating) as avg_rating
        FROM discount_data
        GROUP BY 1
        ORDER BY 
            CASE discount_range 
                WHEN 'No Discount' THEN 1
                WHEN '1-25%' THEN 2
                WHEN '26-50%' THEN 3
                ELSE 4
            END
    """)
    analytics["discount_analysis"]["ranges"] = [
        {
            "discount_range": row[0],
            "product_count": row[1],
            "avg_rating": round(row[2], 2) if row[2] is not None else None
        }
        for row in cursor.fetchall()
    ]

    # 2. Rating Analysis
    cursor.execute(f"""
        WITH rating_data AS (
            SELECT 
                CAST(json_extract_string(extracted_product, '$.rating.average_rating') AS FLOAT) as rating,
                CAST(json_extract_string(extracted_product, '$.rating.rating_count') AS INTEGER) as count,
                CAST(json_extract_string(extracted_product, '$.price_info.price') AS FLOAT) as price
            FROM {table_name}
            WHERE json_extract_string(extracted_product, '$.rating.average_rating') IS NOT NULL
        )
        SELECT 
            AVG(rating) as avg_rating,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY rating) as median_rating,
            CORR(rating, price) as price_rating_correlation,
            AVG(count) as avg_review_count,
            MAX(count) as max_review_count
        FROM rating_data
    """)
    row = cursor.fetchone()
    analytics["rating_analysis"]["statistics"] = {
        "average_rating": round(row[0], 2) if row[0] is not None else None,
        "median_rating": round(row[1], 2) if row[1] is not None else None,
        "price_rating_correlation": round(row[2], 2) if row[2] is not None else None,
        "average_review_count": round(row[3], 2) if row[3] is not None else None,
        "max_review_count": row[4]
    }

    # 3. Material Analysis
    cursor.execute(f"""
        WITH material_data AS (
            SELECT 
                unnest(string_to_array(trim(both '[]' from json_extract_string(extracted_product, '$.materials')), ',')) as material,
                CAST(json_extract_string(extracted_product, '$.price_info.price') AS FLOAT) as price,
                json_extract_string(extracted_product, '$.brand.name') as brand
            FROM {table_name}
            WHERE json_extract_string(extracted_product, '$.materials') IS NOT NULL
        )
        SELECT 
            material,
            COUNT(*) as count,
            AVG(price) as avg_price,
            LIST(DISTINCT brand) as brands
        FROM material_data
        WHERE material IS NOT NULL
        GROUP BY material
        ORDER BY count DESC
        LIMIT 10
    """)
    analytics["material_analysis"]["popular_materials"] = [
        {
            "name": row[0],
            "count": row[1],
            "avg_price": round(row[2], 2),
            "top_brands": row[3][:5] if row[3] else []  # Limit to top 5 brands
        }
        for row in cursor.fetchall()
    ]

    # 4. Brand Analysis
    cursor.execute(f"""
        WITH brand_data AS (
            SELECT 
                json_extract_string(extracted_product, '$.brand.name') as brand,
                CAST(json_extract_string(extracted_product, '$.price_info.price') AS FLOAT) as price,
                CAST(json_extract_string(extracted_product, '$.rating.average_rating') AS FLOAT) as rating
            FROM {table_name}
            WHERE json_extract_string(extracted_product, '$.brand.name') IS NOT NULL
        )
        SELECT 
            brand,
            COUNT(*) as product_count,
            MIN(price) as min_price,
            MAX(price) as max_price,
            AVG(price) as avg_price,
            AVG(rating) as avg_rating
        FROM brand_data
        GROUP BY brand
        HAVING COUNT(*) >= 5
        ORDER BY product_count DESC
        LIMIT 10
    """)
    analytics["brand_analysis"]["top_brands"] = [
        {
            "name": row[0],
            "product_count": row[1],
            "price_range": {
                "min": round(row[2], 2),
                "max": round(row[3], 2),
                "avg": round(row[4], 2)
            },
            "avg_rating": round(row[5], 2) if row[5] is not None else None
        }
        for row in cursor.fetchall()
    ]

    # 5. Audience Analysis
    cursor.execute(f"""
        WITH audience_data AS (
            SELECT 
                unnest(string_to_array(trim(both '[]' from json_extract_string(extracted_product, '$.audience.genders')), ',')) as gender,
                unnest(string_to_array(trim(both '[]' from json_extract_string(extracted_product, '$.audience.age_groups')), ',')) as age_group,
                CAST(json_extract_string(extracted_product, '$.price_info.price') AS FLOAT) as price
            FROM {table_name}
            WHERE json_extract_string(extracted_product, '$.audience') IS NOT NULL
        )
        SELECT 
            gender,
            age_group,
            COUNT(*) as product_count,
            AVG(price) as avg_price
        FROM audience_data
        WHERE gender IS NOT NULL AND age_group IS NOT NULL
        GROUP BY gender, age_group
        ORDER BY product_count DESC
    """)
    analytics["audience_analysis"]["demographics"] = [
        {
            "gender": row[0],
            "age_group": row[1],
            "product_count": row[2],
            "avg_price": round(row[3], 2)
        }
        for row in cursor.fetchall()
    ]

    # Variant Analysis
    cursor.execute(f"""
        WITH variant_data AS (
            SELECT 
                json_extract_string(extracted_product, '$.hasVariant') as variants_json,
                json_extract_string(extracted_product, '$.price_info.price') as price
            FROM {table_name}
            WHERE json_extract_string(extracted_product, '$.hasVariant') IS NOT NULL
                AND json_extract_string(extracted_product, '$.hasVariant') != '[]'
        ),
        variant_counts AS (
            SELECT 
                CASE 
                    WHEN variants_json IS NULL OR variants_json = '[]' THEN 0
                    ELSE json_array_length(variants_json)
                END as variant_count,
                CAST(price AS FLOAT) as product_price
            FROM variant_data
        )
        SELECT 
            variant_count,
            COUNT(*) as product_count,
            (COUNT(*) * 100.0 / (SELECT COUNT(*) FROM variant_counts))::FLOAT as percentage
        FROM variant_counts
        GROUP BY variant_count
        ORDER BY variant_count
    """)
    analytics["variant_analysis"]["variants"] = [
        {
            "variant_count": row[0],
            "product_count": row[1],
            "percentage": round(row[2], 2)
        }
        for row in cursor.fetchall()
    ]

    # Additional variant statistics
    cursor.execute(f"""
        WITH variant_data AS (
            SELECT 
                json_extract_string(extracted_product, '$.hasVariant') as variants_json,
                CAST(json_extract_string(extracted_product, '$.price_info.price') AS FLOAT) as price
            FROM {table_name}
            WHERE json_extract_string(extracted_product, '$.hasVariant') IS NOT NULL
                AND json_extract_string(extracted_product, '$.hasVariant') != '[]'
                AND json_extract_string(extracted_product, '$.price_info.price') IS NOT NULL
        ),
        variant_stats AS (
            SELECT 
                CASE 
                    WHEN variants_json IS NULL OR variants_json = '[]' THEN 0
                    ELSE json_array_length(variants_json)
                END as variant_count,
                price
            FROM variant_data
        )
        SELECT
            AVG(variant_count) as avg_variants,
            MAX(variant_count) as max_variants,
            CORR(variant_count, price) as price_variant_correlation,
            COUNT(*) as total_products_with_variants
        FROM variant_stats
        WHERE variant_count > 0
    """)
    row = cursor.fetchone()
    analytics["variant_analysis"]["statistics"] = {
        "average_variants": round(row[0], 2) if row[0] is not None else None,
        "max_variants": row[1],
        "price_variant_correlation": round(row[2], 2) if row[2] is not None else None,
        "total_products_with_variants": row[3]
    }

    conn.close()
    return JSONResponse(analytics)