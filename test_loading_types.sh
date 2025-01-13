#!/bin/bash

# Exit on any error
set -e

echo "Loading data from local extraction into Sqlite..."
uv run src/process_catalog.py --catalog anntaylor --local --download /tmp/octogen.extractor
mv anntaylor_catalog.sqlite anntaylor_catalog.sqlite.extractor
echo "✓ First test complete"

echo "Loading data from local extraction into DuckDB..."
uv run src/process_catalog.py --catalog anntaylor --local --download /tmp/octogen.extractor --db-type duckdb
mv anntaylor_catalog.duckdb anntaylor_catalog.duckdb.extractor
echo "✓ Second test complete"

echo "Loading data from GCS exchange into Sqlite..."
uv run src/process_catalog.py --catalog anntaylor
mv anntaylor_catalog.sqlite anntaylor_catalog.sqlite.gcs
echo "✓ Third test complete"

echo "Loading data from GCS exchange into DuckDB..."
uv run src/process_catalog.py --catalog anntaylor --db-type duckdb
mv anntaylor_catalog.duckdb anntaylor_catalog.duckdb.gcs
echo "✓ Fourth tests complete"

echo "Loading data from octogendb dump into Sqlite..."
uv run src/process_catalog.py --catalog anntaylor --local --download /tmp/octogendb-downloader
mv anntaylor_catalog.sqlite anntaylor_catalog.sqlite.octogendb
echo "✓ Fifth tests complete"

echo "Loading data from octogendb dump into DuckDB..."
uv run src/process_catalog.py --catalog anntaylor --db-type duckdb
mv anntaylor_catalog.duckdb anntaylor_catalog.duckdb.octogendb
echo "✓ Sixth tests complete"


echo "All tests completed successfully!"