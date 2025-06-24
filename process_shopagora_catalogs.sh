#!/bin/bash

# Script to download and process shopagora catalogs: gymshark, uniqlo, and guestinresidence

# Set environment variables
export OCTOGEN_CATALOG_BUCKET_NAME=octogen-catalog-exchange
export OCTOGEN_CUSTOMER_NAME=shopagora

# Check if credentials file path is provided as argument
if [ "$1" == "" ]; then
  echo "Please provide the path to the service account key file as an argument"
  echo "Usage: ./process_shopagora_catalogs.sh /path/to/key.json"
  exit 1
fi

# Set credentials path
export GOOGLE_APPLICATION_CREDENTIALS=$1

echo "Processing shopagora catalogs: gymshark, uniqlo, and guestinresidence"

# Process each catalog
echo "Processing gymshark catalog..."
uv run src/process_catalog.py --catalog gymshark

echo "Processing uniqlo catalog..."
uv run src/process_catalog.py --catalog uniqlo

echo "Processing sephora catalog..."
uv run src/process_catalog.py --catalog sephora

echo "All shopagora catalogs processed successfully!"
echo "You can now run './run_api_and_svelte_servers.sh' to start the frontend and backend"
echo "Access the UI at http://localhost:5173/" 