# Octogen Shop Catalog Tools

This repository contains tools to download and work with the Octogen shopping catalogs. The instructions here have been tested on MacOS, but
not on Windows.

## Getting Started

### 1. Install UV

Please follow instructions [here](https://docs.astral.sh/uv/getting-started/installation/) for your platform.

### 2. Setup environment

Create a `.env` file in the root directory with the following env vars.
Please obtain the customer name and service account credentials file from your Octogen Account rep.

```
OCTOGEN_CATALOG_BUCKET_NAME=octogen-catalog-exchange
OCTOGEN_CUSTOMER_NAME=<octogen-customer-name>
GOOGLE_APPLICATION_CREDENTIALS=<Path to the Service Account credentials file>
```

### 3. Download catalog

Run the following command to download a catalog.

```
uv run src/octogen_catalog.py --catalog <catalog-name> --download <download-path>
```
eg:
```
uv run src/octogen_catalog.py --catalog anntaylor --download /tmp/octogen-catalog-exchange
uv run src/octogen_catalog.py --catalog chairish --download /tmp/octogen-catalog-exchange
uv run src/octogen_catalog.py --catalog heydude --download /tmp/octogen-catalog-exchange
```
Now the catalog files will be downloaded to `/tmp/octogen-catalog-exchange/<OCTOGEN_CUSTOMER_NAME>/catalog=<catalog-name>/`: 
```
ls /tmp/octogen-catalog-exchange/velou/catalog=anntaylor/
```

### 4. Extract the data to a database

I had the AI generate a script to load the data to a SQLite database:
```
uv run src/load_to_db.py --catalog anntaylor --download /tmp/octogen-catalog-exchange
uv run src/load_to_db.py --catalog heydude --download /tmp/octogen-catalog-exchange
uv run src/load_to_db.py --catalog chairish --download /tmp/octogen-catalog-exchange
```

### 5. Query the data
I used https://sqlitebrowser.org/, which I installed via `brew install sqlitebrowser`.

```
brew install sqlitebrowser
```
Open the application and select the database file `anntaylor_catalog.db`. 

The datastructure for each product is simple: a `product_url`, `id`, `name` and `extracted_product` json column/field that has all of the
attributes. 

The schema for `extracted_product` is in `src/schema.py` and a json version of it is in `src/schema.json`.

### 6. Alternative query: read structured products 

We've also included a script to read the structured products into a pandas dataframe and print them out in tabular format:
```
uv run src/read_structured_products.py --catalog anntaylor --db_path anntaylor_catalog.db
```

### 7. Run a sample UI! 

I've included a sample UI in `src/app/src/App.svelte`. To run it, you can use the following command.

First, you will need to make sure you have installed `npm`: 
```
brew install npm
```

Then run the shell script, which will install all dependencies and start the FastAPI server and the Svelte server:

```
chmod +x run_api_and_svelte_server.sh
./run_api_and_svelte_server.sh
```

This should output something like:
```
  VITE v5.4.11  ready in 293 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
INFO:     127.0.0.1:53403 - "GET /api/anntaylor/products?page=1&per_page=100 HTTP/1.1" 200 OK
```
Open up your browser and go to `http://localhost:5173/`. You should see a list of products. You can click on the product to see variants etc.
