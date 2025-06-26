#!/bin/bash

# Function to discover and process catalogs
discover_and_process_catalogs() {
    echo "Discovering and processing catalogs from GCS..."
    echo "This may take a few minutes depending on the catalog size."
    
    # Run the Python script to discover and process catalogs
    uv run discover_and_process_catalogs.py
    
    # Check if the script was successful
    if [ $? -ne 0 ]; then
        echo "Error: Failed to discover and process catalogs."
        echo "Please check your .env configuration and GCS credentials."
        echo "You can continue without catalog processing, but the application may not work correctly."
        read -p "Do you want to continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Exiting..."
            exit 1
        fi
    else
        echo "Catalog processing completed successfully."
    fi
}

# Function to build the Svelte app
build_svelte_app() {
    echo "Building Svelte app..."
    cd src/app
    npm install
    npm run build
    cd ../../
}

# Function to run the Vite dev server
run_vite_server() {
    echo "Starting Vite dev server..."
    cd src/app
    npm run dev &
    cd ../../
}

# Function to run the FastAPI server
run_fastapi_server() {
    echo "Starting FastAPI server..."
    uv run -m uvicorn src.backend:app --reload --port 8000 --workers 2
}

# Trap SIGINT to kill background processes and their children
trap 'pkill -P $$; exit' SIGINT

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found."
    echo "Please create a .env file based on .env.example"
    exit 1
fi

# Check Python dependencies
check_python_dependencies

# Discover and process catalogs before starting servers
discover_and_process_catalogs

# Build the Svelte app
build_svelte_app

# Run both servers
run_vite_server
run_fastapi_server


# Wait for all background processes
wait 
