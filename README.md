# Shop Catalog Tools

A powerful tool for downloading, processing, and visualizing product catalog data from Google Cloud Storage. This application provides a web-based interface to browse and search through product catalogs with an intuitive user experience.

## Prerequisites

Before you begin, ensure you have the following installed:
- Python 3.8 or higher
- Node.js 16 or higher
- npm package manager
- [uv](https://github.com/astral-sh/uv) - Python package installer

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/octogen-ai/shop-catalog-tools.git
```

```bash
cd shop-catalog-tools
```

### 2. Configure Google Cloud Credentials

You'll need to set up Google Cloud credentials to access your catalog data from Google Cloud Storage.

1. Obtain your service account JSON file from an Octogen Admin
2. Place the JSON file in a secure location on your system (e.g., in the project directory)
3. Copy the example environment file and update it with your settings:

```bash
cp .env.example .env
```

4. Edit the `.env` file to set your credentials path:

```
# IMPORTANT: Use absolute path, not ~/path
GOOGLE_APPLICATION_CREDENTIALS="/absolute/path/to/your/service-account-key.json"
```

### 3. Configure Catalog Settings

In the same `.env` file, configure your catalog settings:

```
OCTOGEN_CATALOG_BUCKET_NAME="your-gcs-bucket-name" //use the same one in the example env file
OCTOGEN_CUSTOMER_NAME="your-shop-id" //shared with you by an Octogen Admin
```

These environment variables are required for the application to automatically discover and process catalogs.

## Running the Application

The simplest way to run the application is to use our all-in-one script:

```bash
chmod +x run_api_and_svelte_servers.sh
./run_api_and_svelte_servers.sh
```

This script will:
1. Check for required Python dependencies
2. Automatically discover and process catalogs from Google Cloud Storage. The first time this happens, it may take a minute.
3. Install all necessary frontend dependencies
4. Build the Svelte application
5. Start the Vite development server
6. Start the FastAPI backend server

Once running, you can access the application at `http://localhost:5173` in your browser.

To stop the application, press `Ctrl+C` in the terminal.

## Automatic Catalog Discovery and Processing

The application now features automatic catalog discovery and processing at startup:

1. When the application starts, it will:
   - Automatically discover available catalogs in Google Cloud Storage
   - Process missing catalogs before starting the servers
   - Display a status message showing progress

2. This ensures that:
   - All catalogs are available when the UI loads
   - No manual intervention is required to process catalogs
   - The application is immediately usable with all available data

This feature eliminates the need to manually run processing scripts for each catalog.

## Using the Frontend

### Navigation

1. **Catalog Selection**: Use the dropdown in the navigation bar to switch between different catalogs
2. **Product Browsing**: The main page displays all products in a grid layout with infinite scrolling

### Search Functionality

The search bar supports multiple search modes:

1. **Regular Search**: Type any keyword to search across product names and descriptions
   ```
   Example: "shoes"
   ```
2. **Clear Search**: Click the X icon in the search field to clear your search

### Product Details

- Click on any product card to view detailed information
- The product overview includes:
  - Multiple product images with navigation
  - Price information
  - Product description
  - Ratings and reviews
  - Size and color options
  - Link to view on retailer site
  - Raw JSON data viewer

### Features

- **Infinite Scrolling**: Products load automatically as you scroll
- **Product Details Modal**: Click any product for a detailed view
- **JSON Data Viewer**: Technical users can view raw product data from modals
- **Automatic Catalog Processing**: The application automatically processes catalogs at startup
