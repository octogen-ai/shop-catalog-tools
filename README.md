# Octogen Shop Catalog Tools

This repository contains tools to download and work with the Octogen shopping catalogs.

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
