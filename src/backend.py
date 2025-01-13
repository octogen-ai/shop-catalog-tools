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
import multiprocessing

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
    
    if not isinstance(conn, duckdb.DuckDBPyConnection):
        return JSONResponse({
            "error": "Analytics are only available with DuckDB database engine",
            "requires_duckdb": True
        })
    
    # More generous memory settings for a 24GB system
    cpu_count = multiprocessing.cpu_count()
    conn.execute(f"SET threads TO {cpu_count}")
    conn.execute("SET memory_limit='16GB'")  # Use up to 16GB of your 24GB
    conn.execute("PRAGMA temp_directory='/tmp'")
    
    # Create a view instead of temp table
    conn.execute(f"""
        CREATE VIEW IF NOT EXISTS product_view AS
        SELECT 
            json_extract_string(extracted_product, '$.id') as id,
            json_extract_string(extracted_product, '$.brand.name') as brand_name,
            json_extract_string(extracted_product, '$.image') as product_image,
            json_extract_string(extracted_product, '$.hasVariant') as variants_json,
            TRY_CAST(json_extract_string(extracted_product, '$.price_info.price') AS FLOAT) as price,
            TRY_CAST(json_extract_string(extracted_product, '$.price_info.original_price') AS FLOAT) as original_price,
            TRY_CAST(json_extract_string(extracted_product, '$.rating.average_rating') AS FLOAT) as rating,
            TRY_CAST(json_extract_string(extracted_product, '$.rating.rating_count') AS INTEGER) as rating_count,
            json_extract_string(extracted_product, '$.materials') as materials,
            json_extract_string(extracted_product, '$.audience.genders') as genders,
            json_extract_string(extracted_product, '$.audience.age_groups') as age_groups,
            json_extract_string(extracted_product, '$.description') as description,
            json_extract_string(extracted_product, '$.name') as name
        FROM {table_name}
    """)

    # Define CTEs for analytics
    stats_ctes = """
        WITH basic_stats AS (
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT brand_name) as unique_brands,
                AVG(CASE WHEN price IS NOT NULL THEN 1 ELSE 0 END) * 100 as price_completeness
            FROM product_view
        ),
        uniqueness_analysis AS (
            SELECT struct_pack(
                brand_name := struct_pack(
                    unique_values := COUNT(DISTINCT brand_name),
                    total_values := COUNT(brand_name)
                ),
                name := struct_pack(
                    unique_values := COUNT(DISTINCT name),
                    total_values := COUNT(name)
                ),
                description := struct_pack(
                    unique_values := COUNT(DISTINCT description),
                    total_values := COUNT(description)
                )
            ) as field_uniqueness
            FROM product_view
        ),
        null_analysis AS (
            SELECT struct_pack(
                brand_name := struct_pack(
                    null_percentage := ROUND(100.0 * COUNT(CASE WHEN brand_name IS NULL THEN 1 END) / COUNT(*), 2)
                ),
                name := struct_pack(
                    null_percentage := ROUND(100.0 * COUNT(CASE WHEN name IS NULL THEN 1 END) / COUNT(*), 2)
                ),
                description := struct_pack(
                    null_percentage := ROUND(100.0 * COUNT(CASE WHEN description IS NULL THEN 1 END) / COUNT(*), 2)
                )
            ) as field_nulls
            FROM product_view
        ),
        variant_stats AS (
            SELECT 
                CASE 
                    WHEN variants_json IS NULL OR variants_json = '[]' THEN 0
                    ELSE json_array_length(variants_json)
                END as variant_count,
                COUNT(*) as product_count,
                ROUND(AVG(price), 2) as avg_price
            FROM product_view
            GROUP BY 1
        ),
        discount_stats AS (
            SELECT 
                CASE 
                    WHEN original_price IS NULL OR price >= original_price THEN 'No Discount'
                    WHEN ((original_price - price) / original_price * 100) < 25 THEN '1-25%'
                    WHEN ((original_price - price) / original_price * 100) < 50 THEN '26-50%'
                    ELSE '50%+'
                END as discount_range,
                COUNT(*) as product_count,
                ROUND(AVG(rating), 2) as avg_rating
            FROM product_view
            GROUP BY 1
        ),
        rating_stats AS (
            SELECT 
                ROUND(AVG(rating), 2) as avg_rating,
                ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY rating), 2) as median_rating,
                ROUND(CORR(rating, price), 2) as price_rating_correlation,
                ROUND(AVG(rating_count), 2) as avg_review_count,
                MAX(rating_count) as max_review_count
            FROM product_view
            WHERE rating IS NOT NULL
        ),
        material_stats AS (
            SELECT 
                m.value as material,
                COUNT(*) as count,
                ROUND(AVG(price), 2) as avg_price,
                array_agg(DISTINCT brand_name) as brands
            FROM product_view,
                 UNNEST(string_to_array(trim(both '[]' from materials), ',')) as m(value)
            WHERE materials IS NOT NULL AND brand_name IS NOT NULL
            GROUP BY 1
            ORDER BY count DESC
            LIMIT 10
        ),
        brand_stats AS (
            SELECT 
                brand_name,
                COUNT(*) as product_count,
                ROUND(MIN(price), 2) as min_price,
                ROUND(MAX(price), 2) as max_price,
                ROUND(AVG(price), 2) as avg_price,
                ROUND(AVG(rating), 2) as avg_rating
            FROM product_view
            WHERE brand_name IS NOT NULL
            GROUP BY 1
            HAVING COUNT(*) >= 5
            ORDER BY product_count DESC
            LIMIT 10
        ),
        audience_stats AS (
            SELECT 
                g.value as gender,
                a.value as age_group,
                COUNT(*) as product_count,
                ROUND(AVG(price), 2) as avg_price
            FROM product_view,
                 UNNEST(string_to_array(trim(both '[]' from genders), ',')) as g(value),
                 UNNEST(string_to_array(trim(both '[]' from age_groups), ',')) as a(value)
            WHERE genders IS NOT NULL AND age_groups IS NOT NULL
            GROUP BY 1, 2
            ORDER BY product_count DESC
        ),
        image_analysis AS (
            SELECT 
                COUNT(CASE WHEN product_image IS NULL THEN 1 END) as null_product_images,
                ROUND(100.0 * COUNT(CASE WHEN product_image IS NULL THEN 1 END) / COUNT(*), 2) as null_product_images_percentage,
                AVG(CASE 
                    WHEN variants_json IS NOT NULL AND variants_json != '[]' 
                    THEN json_array_length(variants_json)
                    ELSE 0 
                END) as avg_variant_images,
                MAX(CASE 
                    WHEN variants_json IS NOT NULL AND variants_json != '[]' 
                    THEN json_array_length(variants_json)
                    ELSE 0 
                END) as max_variant_images,
                MIN(CASE 
                    WHEN variants_json IS NOT NULL AND variants_json != '[]' 
                    THEN json_array_length(variants_json)
                    ELSE 0 
                END) as min_variant_images
            FROM product_view
        )
    """

    # Final select statement
    final_select = """
        SELECT struct_pack(
            basic_analytics := (SELECT struct_pack(
                total_records := total_records,
                unique_brands := unique_brands,
                price_completeness := price_completeness,
                uniqueness_analysis := (SELECT field_uniqueness FROM uniqueness_analysis),
                null_analysis := (SELECT field_nulls FROM null_analysis),
                image_analysis := (SELECT struct_pack(
                    null_product_images := null_product_images,
                    null_product_images_percentage := null_product_images_percentage,
                    avg_variant_images := avg_variant_images,
                    max_variant_images := max_variant_images,
                    min_variant_images := min_variant_images
                ) FROM image_analysis)
            ) FROM basic_stats),
            advanced_analytics := struct_pack(
                variant_analysis := struct_pack(
                    variants := (SELECT array_agg(struct_pack(
                        variant_count := variant_count,
                        product_count := product_count,
                        avg_price := avg_price
                    ) ORDER BY product_count DESC) FROM variant_stats),
                    statistics := struct_pack(
                        avg_variants := (SELECT AVG(variant_count) FROM variant_stats WHERE variant_count > 0),
                        max_variants := (SELECT MAX(variant_count) FROM variant_stats),
                        total_products_with_variants := (SELECT SUM(product_count) FROM variant_stats WHERE variant_count > 0)
                    )
                ),
                discount_analysis := struct_pack(
                    ranges := (SELECT array_agg(struct_pack(
                        discount_range := discount_range,
                        product_count := product_count,
                        avg_rating := avg_rating
                    )) FROM discount_stats)
                ),
                rating_analysis := struct_pack(
                    statistics := (SELECT struct_pack(
                        avg_rating := avg_rating,
                        median_rating := median_rating,
                        price_rating_correlation := price_rating_correlation,
                        avg_review_count := avg_review_count,
                        max_review_count := max_review_count
                    ) FROM rating_stats)
                ),
                material_analysis := struct_pack(
                    popular_materials := (SELECT array_agg(struct_pack(
                        material := material,
                        count := count,
                        avg_price := avg_price,
                        brands := brands
                    )) FROM material_stats)
                ),
                brand_analysis := struct_pack(
                    top_brands := (SELECT array_agg(struct_pack(
                        name := brand_name,
                        product_count := product_count,
                        min_price := min_price,
                        max_price := max_price,
                        avg_price := avg_price,
                        avg_rating := avg_rating
                    )) FROM brand_stats)
                ),
                audience_analysis := CASE 
                    WHEN (SELECT COUNT(*) FROM audience_stats) > 0 
                    THEN struct_pack(
                        demographics := (SELECT array_agg(struct_pack(
                            gender := gender,
                            age_group := age_group,
                            product_count := product_count,
                            avg_price := avg_price
                        )) FROM audience_stats)
                    )
                    ELSE NULL
                END
            )
        )::json as analytics
    """

    # Combine all parts
    analytics_query = stats_ctes + final_select

    # Execute the combined query
    cursor = conn.cursor()
    cursor.execute(analytics_query)
    result = cursor.fetchone()[0]
    
    conn.close()
    return JSONResponse({
        "requires_duckdb": True,
        **json.loads(result)
    })

@app.get("/api/catalogs")
async def get_catalogs():
    load_dotenv()
    db_engine = os.getenv('DB_ENGINE', 'sqlite').lower()
    base_dir = os.path.join(os.path.dirname(__file__), "..")
    
    extension = 'duckdb' if db_engine == 'duckdb' else 'sqlite'
    alt_extension = 'db' if extension == 'sqlite' else None
    
    catalogs = []
    for file in os.listdir(base_dir):
        if file.endswith(f'_catalog.{extension}'):
            catalog = file.replace(f'_catalog.{extension}', '')
            catalogs.append(catalog)
        elif alt_extension and file.endswith(f'_catalog.{alt_extension}'):
            catalog = file.replace(f'_catalog.{alt_extension}', '')
            catalogs.append(catalog)
    
    return JSONResponse({
        "catalogs": sorted(list(set(catalogs)))
    })
