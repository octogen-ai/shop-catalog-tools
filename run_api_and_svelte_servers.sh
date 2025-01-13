#!/bin/bash

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

# Build the Svelte app
build_svelte_app

# Run both servers
run_vite_server
run_fastapi_server

# Wait for all background processes
wait 