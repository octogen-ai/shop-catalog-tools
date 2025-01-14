import json
import math
import multiprocessing
import os
from pathlib import Path

import duckdb
import yaml
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from whoosh.index import open_dir
from whoosh.qparser import MultifieldParser

app = FastAPI()

# Serve the Svelte app
app.mount("/static", StaticFiles(directory="src/app/dist", html=True), name="app")


# Database connection
def get_db_connection(table_name: str) -> duckdb.DuckDBPyConnection:
    """Get a DuckDB database connection."""
    db_path = os.path.join(
        os.path.dirname(__file__), "..", f"{table_name}_catalog.duckdb"
    )
    if not os.path.exists(db_path):
        raise HTTPException(
            status_code=404,
            detail=f"Database {table_name}_catalog.duckdb not found",
        )
    return duckdb.connect(db_path)


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
    cursor.execute(
        f"""
        SELECT extracted_product FROM {table_name}
        WHERE json_extract(extracted_product, '$.id') IS NOT NULL
        LIMIT ? OFFSET ?
    """,
        (per_page, (page - 1) * per_page),
    )
    products = cursor.fetchall()
    conn.close()

    return JSONResponse(
        {
            "products": [
                json.loads(
                    row[0]
                    if isinstance(conn, duckdb.DuckDBPyConnection)
                    else row["extracted_product"]
                )
                for row in products
            ],
            "total": total_count,
            "page": page,
            "per_page": per_page,
            "total_pages": math.ceil(total_count / per_page),
        }
    )


@app.get("/api/{table_name}/search")
async def search_products(
    table_name: str, query: str, page: int = 1, per_page: int = 12
):
    # Open Whoosh index
    index_dir = f"/tmp/whoosh/{table_name}"
    if not os.path.exists(index_dir):
        raise HTTPException(
            status_code=404, detail=f"Search index not found for {table_name}"
        )

    ix = open_dir(index_dir)

    # Get only searchable fields from the schema (those with a format/analyzer)
    searchable_fields = [
        name
        for name, field in ix.schema.items()
        if hasattr(field, "format") and field.format
    ]
    print(
        f"Searchable fields: {searchable_fields}"
    )  # Debug print to see available fields

    parser = MultifieldParser(searchable_fields, schema=ix.schema)
    parsed_query = parser.parse(query)

    with ix.searcher() as searcher:
        results = searcher.search_page(parsed_query, page, pagelen=per_page)
        total_count = results.total

        # Get both ID fields from search results
        product_ids = []
        for result in results:
            if "productGroupID" in result:
                product_ids.append(result["productGroupID"])
            elif "id" in result:
                product_ids.append(result["id"])

        print(
            f"Found {total_count} total products, returning page {page} for query: {query}"
        )
        print(f"Product IDs from search: {product_ids}")  # Debug print

    if not product_ids:
        return JSONResponse(
            {
                "products": [],
                "total": 0,
                "page": page,
                "per_page": per_page,
                "total_pages": 0,
            }
        )

    # Get full product data from database
    conn = get_db_connection(table_name)
    placeholders = ",".join(["?" for _ in product_ids])

    cursor = conn.cursor()
    # Query using both ID fields with correct column name
    products = cursor.execute(
        f"""
        SELECT extracted_product 
        FROM {table_name} 
        WHERE json_extract(extracted_product, '$.id') IN ({placeholders})
        OR product_group_id IN ({placeholders})
    """,
        product_ids + product_ids,
    ).fetchall()

    print(f"Found {len(products)} products in database")  # Debug print

    conn.close()

    return JSONResponse(
        {
            "products": [
                json.loads(
                    row[0]
                    if isinstance(conn, duckdb.DuckDBPyConnection)
                    else row["extracted_product"]
                )
                for row in products
            ],
            "total": total_count,
            "page": page,
            "per_page": per_page,
            "total_pages": math.ceil(total_count / per_page),
        }
    )


def format_yaml_as_html(yaml_str: str) -> str:
    lines = yaml_str.split("\n")
    processed_lines = []

    for line in lines:
        if ":" in line:
            # Split on first colon and handle attribute names
            attr_name, value = line.split(":", 1)
            if "url" in attr_name:
                # Handle URL values specially
                url = value.strip()
                processed_lines.append(
                    f'<strong>{attr_name}</strong>: <a href="{url}">{url}</a>'
                )
            else:
                # Make regular attributes bold
                processed_lines.append(f"<strong>{attr_name}</strong>:{value}")
        else:
            processed_lines.append(line)

    return "<pre>" + "\n".join(processed_lines) + "</pre>"


@app.get("/api/{table}/product/{product_id}/raw")
async def get_raw_product(
    request: Request, table: str, product_id: str, format: str = "json"
):
    conn = get_db_connection(table)
    cursor = conn.cursor()

    cursor.execute(
        f"SELECT extracted_product FROM {table} WHERE product_group_id = ?",
        (product_id,),
    )
    result = cursor.fetchone()
    conn.close()

    if not result:
        raise HTTPException(status_code=404, detail="Product not found")

    data = json.loads(result[0])
    formats = {"json": "JSON", "yaml": "YAML", "tree": "Tree View"}

    template_context = {
        "request": request,
        "formats": formats,
        "current_format": format.lower(),
        "format": format.lower(),
        "json_data": json.dumps(data),
    }

    if format.lower() == "yaml":
        yaml_str = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
        template_context["content"] = format_yaml_as_html(yaml_str)
    elif format.lower() == "json":
        template_context["content"] = json.dumps(data, indent=2)

    return templates.TemplateResponse("product_view.html", template_context)


@app.get("/api/{table_name}/analytics")
async def get_table_analytics(table_name: str):
    conn = get_db_connection(table_name)

    if not isinstance(conn, duckdb.DuckDBPyConnection):
        return JSONResponse(
            {
                "error": "Analytics are only available with DuckDB database engine",
                "requires_duckdb": True,
            }
        )

    # Configure DuckDB for external aggregation
    cpu_count = multiprocessing.cpu_count()
    conn.execute(f"PRAGMA threads={cpu_count}")
    conn.execute(f"PRAGMA external_threads={max(1, cpu_count - 1)}")
    conn.execute("PRAGMA memory_limit='8GB'")
    conn.execute("PRAGMA temp_directory='/tmp'")

    # Use the pre-extracted fields directly
    stats_ctes = """
        WITH basic_stats AS (
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT brand_name) as unique_brands,
                AVG(CASE WHEN price IS NOT NULL THEN 1 ELSE 0 END) * 100 as price_completeness
            FROM {table_name}_extracted
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
            FROM {table_name}_extracted
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
            FROM {table_name}_extracted
        ),
        variant_stats AS (
            SELECT 
                CASE 
                    WHEN variants_json IS NULL OR variants_json = '[]' THEN 0
                    ELSE json_array_length(variants_json)
                END as variant_count,
                COUNT(*) as product_count,
                ROUND(AVG(price), 2) as avg_price
            FROM {table_name}_extracted
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
            FROM {table_name}_extracted
            GROUP BY 1
        ),
        rating_stats AS (
            SELECT 
                ROUND(AVG(rating), 2) as avg_rating,
                ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY rating), 2) as median_rating,
                ROUND(CORR(rating, price), 2) as price_rating_correlation,
                ROUND(AVG(rating_count), 2) as avg_review_count,
                MAX(rating_count) as max_review_count
            FROM {table_name}_extracted
            WHERE rating IS NOT NULL
        ),
        material_stats AS (
            SELECT 
                m.value as material,
                COUNT(*) as count,
                ROUND(AVG(price), 2) as avg_price,
                array_agg(DISTINCT brand_name) as brands
            FROM {table_name}_extracted,
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
            FROM {table_name}_extracted
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
            FROM {table_name}_extracted,
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
            FROM {table_name}_extracted
        ),
        additional_attr_stats AS (
            SELECT 
                attr_name,
                COUNT(DISTINCT product_id) as occurrence_count,
                COUNT(DISTINCT attr_value) as unique_values,
                ROUND(100.0 * COUNT(DISTINCT product_id) / (
                    SELECT COUNT(*) 
                    FROM {table_name}_extracted 
                    WHERE additional_attributes_json IS NOT NULL
                ), 2) as coverage_percentage,
                array_agg(DISTINCT attr_value) as value_samples
            FROM {table_name}_additional_attrs
            GROUP BY attr_name
            HAVING COUNT(DISTINCT product_id) >= 5
                AND COUNT(DISTINCT attr_value) > 1
            ORDER BY occurrence_count DESC
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
                END,
                additional_attributes_analysis := struct_pack(
                    attributes := (
                        SELECT array_agg(struct_pack(
                            name := attr_name,
                            occurrence_count := occurrence_count,
                            unique_values := unique_values,
                            coverage_percentage := coverage_percentage,
                            value_samples := value_samples
                        ))
                        FROM additional_attr_stats
                    ),
                    statistics := struct_pack(
                        total_attributes := (SELECT COUNT(DISTINCT attr_name) FROM additional_attr_stats),
                        avg_attributes_per_product := (
                            SELECT AVG(
                                array_length(
                                    string_to_array(
                                        CASE 
                                            WHEN additional_attributes_json IS NULL THEN ''
                                            ELSE trim(both '{}' from additional_attributes_json)
                                        END,
                                        ','
                                    )
                                )
                            )
                            FROM {table_name}_extracted
                            WHERE additional_attributes_json IS NOT NULL
                                AND additional_attributes_json != 'null'
                                AND additional_attributes_json != '{}'
                        ),
                        products_with_attributes := (
                            SELECT COUNT(*)
                            FROM {table_name}_extracted
                            WHERE additional_attributes_json IS NOT NULL
                                AND additional_attributes_json != 'null'
                                AND additional_attributes_json != '{}'
                        )
                    )
                )
            )
        )::json as analytics
    """

    # Combine all parts
    analytics_query = stats_ctes + final_select
    analytics_query = analytics_query.replace("{table_name}", table_name)

    # Execute the combined query
    cursor = conn.cursor()
    cursor.execute(analytics_query)
    result = cursor.fetchone()[0]

    conn.close()
    return JSONResponse({"requires_duckdb": True, **json.loads(result)})


@app.get("/api/catalogs")
async def get_catalogs():
    load_dotenv()
    base_dir = os.path.join(os.path.dirname(__file__), "..")
    extension = "duckdb"
    catalogs = []
    for file in os.listdir(base_dir):
        if file.endswith(f"_catalog.{extension}"):
            catalog = file.replace(f"_catalog.{extension}", "")
            catalogs.append(catalog)
    return JSONResponse({"catalogs": sorted(list(set(catalogs)))})
