import json
import math
import multiprocessing
import os

import duckdb
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from whoosh.index import open_dir
from whoosh.qparser import MultifieldParser

app = FastAPI()

# Serve the Svelte app
# and the vendor files
app.mount("/static", StaticFiles(directory="src/app/dist", html=True), name="app")


# Database connection
def get_db_connection(table_name: str) -> duckdb.DuckDBPyConnection:
    """Get a DuckDB database connection.

    Args:
        table_name (str): Name of the table/catalog to connect to

    Returns:
        duckdb.DuckDBPyConnection: Database connection object

    Raises:
        HTTPException: If database file is not found
    """
    db_path = os.path.join(
        os.path.dirname(__file__), "..", f"{table_name}_catalog.duckdb"
    )
    if not os.path.exists(db_path):
        raise HTTPException(
            status_code=404,
            detail=f"Database {table_name}_catalog.duckdb not found",
        )
    return duckdb.connect(db_path)


@app.get("/")
async def root():
    """Serve the main application page.

    Returns:
        FileResponse: The main index.html file
    """
    return FileResponse("src/app/dist/index.html")


@app.get("/api/{table_name}/products")
async def get_products(table_name: str, page: int = 1, per_page: int = 12):
    """Get paginated products from the specified catalog.

    Args:
        table_name (str): Name of the catalog/table to query
        page (int, optional): Page number. Defaults to 1.
        per_page (int, optional): Number of items per page. Defaults to 12.

    Returns:
        JSONResponse: Paginated products with metadata
    """
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
    """Search products in the specified catalog using Whoosh index.

    Args:
        table_name (str): Name of the catalog to search
        query (str): Search query string
        page (int, optional): Page number. Defaults to 1.
        per_page (int, optional): Number of items per page. Defaults to 12.

    Returns:
        JSONResponse: Search results with pagination metadata

    Raises:
        HTTPException: If search index is not found
    """
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

    try:
        # Modify the database query to handle malformed JSON
        cursor = conn.cursor()
        query_sql = f"""
        SELECT extracted_product 
        FROM {table_name} 
        WHERE TRY_CAST(json_extract(extracted_product, '$.id') AS VARCHAR) IN ({placeholders})
        OR TRY_CAST(product_group_id AS VARCHAR) IN ({placeholders})
        """
        products = cursor.execute(query_sql, product_ids + product_ids).fetchall()

        # Add validation when parsing JSON
        valid_products = []
        for row in products:
            try:
                product_data = json.loads(
                    row[0]
                    if isinstance(conn, duckdb.DuckDBPyConnection)
                    else row["extracted_product"]
                )
                valid_products.append(product_data)
            except json.JSONDecodeError:
                print(f"Skipping invalid JSON product: {row[0]}")
                continue

        print(f"Found {len(valid_products)} valid products in database")  # Debug print

        return JSONResponse(
            {
                "products": valid_products,
                "total": total_count,
                "page": page,
                "per_page": per_page,
                "total_pages": math.ceil(total_count / per_page),
            }
        )

    except Exception as e:
        print(f"Search error: {str(e)}")  # Debug print
        return JSONResponse(
            {
                "products": [],
                "total": 0,
                "page": page,
                "per_page": per_page,
                "total_pages": 0,
                "error": "Search failed due to data integrity issues",
            },
            status_code=200,  # Return empty results instead of 500 error
        )
    finally:
        conn.close()


@app.get("/api/{table}/product/{product_group_id}/data")
async def get_product_data(table: str, product_group_id: str):
    """Get raw product data.

    Args:
        table (str): Catalog/table name
        product_id (str): Product identifier

    Returns:
        JSONResponse: Product data

    Raises:
        HTTPException: If product is not found
    """
    conn = get_db_connection(table)
    cursor = conn.cursor()

    cursor.execute(
        f"SELECT extracted_product FROM {table} WHERE product_group_id = ?",
        (product_group_id,),
    )
    result = cursor.fetchone()
    conn.close()

    if not result:
        raise HTTPException(status_code=404, detail="Product not found")

    return JSONResponse(json.loads(result[0]))


@app.get("/api/{table_name}/analytics")
async def get_table_analytics(table_name: str):
    """Generate comprehensive analytics for the specified catalog.

    Args:
        table_name (str): Name of the catalog to analyze

    Returns:
        JSONResponse: Detailed analytics including basic stats, ratings, and brands
    """
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
    stats_ctes = f"""
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
                null_analysis := (SELECT field_nulls FROM null_analysis)
            ) FROM basic_stats),
            advanced_analytics := struct_pack(
                rating_analysis := struct_pack(
                    statistics := (SELECT struct_pack(
                        avg_rating := avg_rating,
                        median_rating := median_rating,
                        price_rating_correlation := price_rating_correlation,
                        avg_review_count := avg_review_count,
                        max_review_count := max_review_count
                    ) FROM rating_stats)
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
                )
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
    return JSONResponse({"requires_duckdb": True, **json.loads(result)})


@app.get("/api/catalogs")
async def get_catalogs():
    """Get list of available catalogs.

    Returns:
        JSONResponse: List of available catalog names
    """
    load_dotenv()
    base_dir = os.path.join(os.path.dirname(__file__), "..")
    extension = "duckdb"
    catalogs = []
    for file in os.listdir(base_dir):
        if file.endswith(f"_catalog.{extension}"):
            catalog = file.replace(f"_catalog.{extension}", "")
            catalogs.append(catalog)
    return JSONResponse({"catalogs": sorted(list(set(catalogs)))})


@app.get("/api/{table_name}/filter")
async def filter_products(
    table_name: str,
    filter_string: str,  # Changed from separate field/operator parameters
    page: int = 1,
    per_page: int = 12,
):
    """Filter products based on field conditions using direct SQL queries.

    Args:
        table_name (str): Name of the catalog to filter
        filter_string (str): Combined filter string (e.g., "rating>3" or "rating:is_null")
        page (int, optional): Page number. Defaults to 1.
        per_page (int, optional): Number of items per page. Defaults to 12.
    """
    conn = get_db_connection(table_name)
    cursor = conn.cursor()

    # Parse the filter string
    if ":" in filter_string:
        # Handle is_null/not_null cases
        field, operator = filter_string.split(":")
        if operator in ["is_null", "not_null"]:
            where_clause = (
                f"{field} IS {'NULL' if operator == 'is_null' else 'NOT NULL'}"
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid operator format")
    else:
        # Handle numeric comparisons
        import re

        match = re.match(r"(\w+)([<>]=?|=)(.+)", filter_string)
        if not match:
            raise HTTPException(status_code=400, detail="Invalid filter format")

        field, comp_operator, value = match.groups()
        try:
            # Validate numeric value
            float(value)
            where_clause = f"{field} {comp_operator} {value}"
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid numeric value")

    # Get total count using the extracted table
    count_query = f"""
        SELECT COUNT(*) 
        FROM {table_name}_extracted
        WHERE {where_clause}
    """
    cursor.execute(count_query)
    total_count = cursor.fetchone()[0]

    # Get paginated results
    query = f"""
        SELECT extracted_product
        FROM {table_name}_extracted
        WHERE {where_clause}
        LIMIT ? OFFSET ?
    """
    cursor.execute(query, (per_page, (page - 1) * per_page))
    products = cursor.fetchall()

    valid_products = []
    for row in products:
        try:
            product_data = json.loads(row[0])
            valid_products.append(product_data)
        except json.JSONDecodeError:
            print(f"Skipping invalid JSON product: {row[0]}")
            continue

    conn.close()

    return JSONResponse(
        {
            "products": valid_products,
            "total": total_count,
            "page": page,
            "per_page": per_page,
            "total_pages": math.ceil(total_count / per_page),
        }
    )


@app.get("/api/{table_name}/crawls")
async def get_crawled_products(table_name: str, product_url: str):
    """Get all crawled data for a specific product URL.

    Args:
        table_name (str): Name of the catalog
        product_url (str): URL of the product to fetch crawl data for

    Returns:
        JSONResponse: List of crawled data entries for the product

    Raises:
        HTTPException: If no crawl data is found
    """
    conn = get_db_connection(table_name)
    cursor = conn.cursor()

    cursor.execute(
        f"""
        SELECT 
            crawl_id,
            catalog,
            product_url,
            crawl_url,
            crawl_timestamp,
            crawl_source,
            api_source,
            octogen_catalog
        FROM {table_name}_crawls 
        WHERE product_url = ?
        ORDER BY crawl_timestamp DESC
        """,
        (product_url,),
    )

    results = cursor.fetchall()
    conn.close()

    if not results:
        raise HTTPException(
            status_code=404, detail=f"No crawl data found for URL: {product_url}"
        )

    crawls = []
    for row in results:
        crawl = {
            "crawl_id": row[0],
            "catalog": row[1],
            "product_url": row[2],
            "crawl_url": row[3],
            "crawl_timestamp": row[4],
            "crawl_source": row[5],
            "api_source": row[6] if row[6] else None,
            "octogen_catalog": row[7],
            "page_content_url": f"/api/{table_name}/crawl/{row[0]}/content",
        }
        crawls.append(crawl)

    return JSONResponse(
        {"product_url": product_url, "crawl_count": len(crawls), "crawls": crawls}
    )


@app.get("/api/{table_name}/crawl/{crawl_id}/content")
async def get_crawl_content(table_name: str, crawl_id: int):
    conn = get_db_connection(table_name)
    cursor = conn.cursor()

    cursor.execute(
        f"""
        SELECT page_content
        FROM {table_name}_crawls 
        WHERE crawl_id = ?
        """,
        (crawl_id,),
    )

    result = cursor.fetchone()
    conn.close()

    if not result:
        raise HTTPException(status_code=404, detail="Crawl content not found")

    return PlainTextResponse(
        content=result[0],
        media_type="text/plain",
        headers={"Content-Disposition": "inline; filename=page_content.txt"},
    )
