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
git clone git@github.com:octogen-ai/shop-catalog-tools.git
cd shop-catalog-tools
```

### 2. Configure Google Cloud Credentials

You'll need to set up Google Cloud credentials to access your catalog data from Google Cloud Storage.

1. Obtain your service account JSON file from an Octogen Admin
2. Place the JSON file in a secure location on your system
3. Set the environment variable to point to your credentials file:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json"
```

### 3. Download Catalog Data

We provide convenient scripts to download catalog data for specific customers:

Your script should look something like...
```bash
./process_{your_shop_id}_catalogs.sh
```

## Running the Application

The simplest way to run the application is to use our all-in-one script:

```bash
chmod +x run_api_and_svelte_servers.sh
./run_api_and_svelte_servers.sh
```

This script will:
1. Install all necessary frontend dependencies
2. Build the Svelte application
3. Start the Vite development server
4. Start the FastAPI backend server

Once running, you can access the application at `http://localhost:5173` in your browser.

To stop the application, press `Ctrl+C` in the terminal.

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
2. **Clear Search**: Click the "Clear search" button or the X icon to return to all products

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

## API Endpoints

The backend provides the following REST API endpoints:

- `GET /api/catalogs` - List all available catalogs
- `GET /api/{catalog}/products` - Get products with pagination
- `GET /api/{catalog}/search?query={query}` - Search products
- `GET /api/{catalog}/filter?filter_string={filter}` - Filter products
- `GET /api/{catalog}/product/{id}` - Get single product details

## License

[Your License Here]

