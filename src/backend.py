from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
import json
import sqlite3
import os
from whoosh.index import open_dir
from whoosh.qparser import QueryParser

app = FastAPI()

# Serve the Svelte app
app.mount("/static", StaticFiles(directory="src/app/dist", html=True), name="app")

# Database connection
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "anntaylor_catalog.db")
INDEX_DIR = "/tmp/whoosh" 
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/")
async def root():
    return FileResponse("src/app/dist/index.html")

@app.get("/api/products")
async def get_products(limit: int = 200):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT extracted_product FROM anntaylor LIMIT ?", (limit,))
    products = cursor.fetchall()
    conn.close()
    return JSONResponse([json.loads(row['extracted_product']) for row in products])

@app.get("/api/search")
async def search_products(query: str):
    ix = open_dir(INDEX_DIR)
    parser = QueryParser("description", schema=ix.schema)
    query = parser.parse(query)

    with ix.searcher() as searcher:
        results = searcher.search(query)
        return JSONResponse([dict(result) for result in results])