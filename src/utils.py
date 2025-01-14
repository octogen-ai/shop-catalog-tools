import os

from fastapi import HTTPException


def get_catalog_db_path(table_name: str, raise_if_not_found: bool = True) -> str:
    """
    Get the path to a catalog's DuckDB database file.

    Args:
        table_name: Name of the catalog/table
        raise_if_not_found: If True, raises HTTPException when file not found

    Returns:
        str: Full path to the DuckDB database file

    Raises:
        HTTPException: If raise_if_not_found is True and the database file doesn't exist
    """
    db_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), f"{table_name}_catalog.duckdb"
    )

    if not os.path.exists(db_path) and raise_if_not_found:
        raise HTTPException(
            status_code=404, detail=f"Database {table_name}_catalog.duckdb not found"
        )

    return db_path
