import glob
import logging
import os
import sys
from typing import Any, Callable, List, MutableMapping

import structlog
from fastapi import HTTPException
from structlog.processors import CallsiteParameter


def get_latest_snapshot_path(folder: str) -> str:
    # If the folder itself is a snapshot, return it
    if os.path.basename(folder).startswith("snapshot="):
        return folder

    # Otherwise, look for snapshot subdirectories
    snapshot_pattern = os.path.join(folder, "snapshot=*")
    snapshot_dirs = sorted(glob.glob(snapshot_pattern), reverse=True)

    if not snapshot_dirs:
        raise ValueError(f"No snapshot directories found in {folder}")

    return snapshot_dirs[0]


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


def configure_logging(
    debug: bool,
    log_to_console: bool,
    loggers: List[str] = [],
    log_probability: float = 1.0,
) -> None:
    shared_processors: List[Callable] = [
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.CallsiteParameterAdder(
            parameters=(CallsiteParameter.FILENAME, CallsiteParameter.LINENO)
        ),
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    structlog.configure(
        processors=shared_processors
        + [
            # probabilistic_processor(log_probability),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    json_log_formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer(),
        ],
    )
    console_log_formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            add_line_number,
            structlog.dev.ConsoleRenderer(colors=True),
        ],
    )

    log_handler = logging.StreamHandler(sys.stdout)
    if log_to_console:
        log_handler.setFormatter(console_log_formatter)
    else:
        log_handler.setFormatter(json_log_formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(log_handler)
    if debug:
        for logger in loggers:
            logging.getLogger(logger).setLevel(logging.DEBUG)
        root_logger.setLevel(logging.DEBUG)
        log_handler.setLevel(logging.DEBUG)
    else:
        for logger in loggers:
            logging.getLogger(logger).setLevel(logging.INFO)
        root_logger.setLevel(logging.INFO)
        log_handler.setLevel(logging.INFO)


def add_line_number(
    logger: Any, method_name: str, event_dict: MutableMapping[str, Any]
) -> MutableMapping[str, Any]:
    """Add the caller's line number to the event dictionary."""
    if "filename" in event_dict and "lineno" in event_dict:
        event_dict["lineno"] = f"[{event_dict['lineno']}]"
    return event_dict
