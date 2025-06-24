#!/bin/bash

# Script to download and process shopari catalogs: gymshark, uniqlo, and sephora

# Set environment variables
export OCTOGEN_CATALOG_BUCKET_NAME=octogen-catalog-exchange
export OCTOGEN_CUSTOMER_NAME=shopari

# Check if credentials file path is provided as argument
if [ "$1" == "" ]; then
  echo "Please provide the path to the service account key file as an argument"
  echo "Usage: ./process_shopari_catalogs.sh /path/to/key.json"
  exit 1
fi

# Set credentials path
export GOOGLE_APPLICATION_CREDENTIALS=$1

echo "Processing shopari catalogs: gymshark, uniqlo, and sephora"

# Process each catalog
echo "Processing gymshark catalog..."
uv run src/process_catalog.py --catalog gymshark

echo "Processing uniqlo catalog..."
uv run src/process_catalog.py --catalog uniqlo

echo "Processing guestinresidence catalog..."
uv run src/process_catalog.py --catalog guestinresidence

echo "All shopari catalogs processed successfully!"
echo "You can now run './run_api_and_svelte_servers.sh' to start the frontend and backend"
echo "Access the UI at http://localhost:5173/" 