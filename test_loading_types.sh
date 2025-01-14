#!/bin/bash

# Exit on any error
set -e

echo "Loading data from local extraction into Duckdb..."
uv run src/process_catalog.py --catalog anntaylor --local --download /tmp/octogen.extractor/anntaylor
mv anntaylor_catalog.duckdb anntaylor_catalog.duckdb.extractor
echo "✓ First test complete"

echo "Loading data from GCS exchange into DuckDB..."
uv run src/process_catalog.py --catalog anntaylor
mv anntaylor_catalog.duckdb anntaylor_catalog.duckdb.gcs
echo "✓ Second tests complete"

echo "Loading data from octogendb dump into Duckdb..."
uv run src/process_catalog.py --catalog anntaylor --local --download /tmp/octogendb-downloader/catalog=anntaylor
mv anntaylor_catalog.duckdb anntaylor_catalog.duckdb.octogendb
echo "✓ Third tests complete"


echo "All tests completed successfully!"