import argparse
import asyncio
import logging
import os

from asyncer import asyncify
from dotenv import load_dotenv
from google.cloud import storage
from google.cloud.storage.blob import Blob

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
# Suppress google-cloud-storage logging
logging.getLogger("google.resumable_media._helpers").setLevel(logging.WARNING)


async def download_blob(
    blob: Blob, download_path: str, semaphore: asyncio.Semaphore, position: int
) -> None:
    async with semaphore:
        full_path = os.path.join(download_path, os.path.dirname(blob.name))
        os.makedirs(full_path, exist_ok=True)
        dest_path = os.path.join(download_path, blob.name)

        from tqdm import tqdm

        CHUNK_SIZE = 1024 * 1024  # 1MB chunks

        # Create progress bar for this file
        desc = f"Downloading {os.path.basename(blob.name)}"
        with tqdm(
            total=blob.size,
            unit="B",
            unit_scale=True,
            desc=desc.ljust(50)[:50],  # Pad description for alignment
            leave=True,  # Keep the progress bar after completion
            dynamic_ncols=True,  # Adapt to terminal width
            position=position,  # Use passed position
            miniters=1,  # Update at least every iteration
            ascii=False,  # Use ASCII characters for the progress bar
        ) as pbar:
            # Download the blob in chunks
            start = 0
            end = blob.size - 1

            with open(dest_path, "wb") as f:
                while start <= end:
                    chunk_end = min(start + CHUNK_SIZE - 1, end)
                    chunk = await asyncify(blob.download_as_bytes)(
                        start=start, end=chunk_end
                    )
                    f.write(chunk)
                    chunk_size = len(chunk)
                    pbar.update(chunk_size)
                    start += chunk_size


async def download_catalog(
    *,
    octogen_catalog_bucket: str,
    octogen_customer_name: str,
    catalog: str,
    download_path: str,
    max_concurrent: int = 4,
) -> None:
    prefix = f"{octogen_customer_name}/catalog={catalog}/"
    logger.info(
        f"Downloading catalog from gs://{octogen_catalog_bucket}/{prefix} to {download_path}"
    )

    storage_client = storage.Client()
    bucket = storage_client.bucket(octogen_catalog_bucket)
    blobs = await asyncify(bucket.list_blobs)(prefix=prefix)

    # Convert to list and filter for .parquet files and snapshots
    blobs = [blob for blob in blobs if blob.name.endswith(".parquet")]

    # Extract snapshots and find the latest one
    import re

    snapshot_pattern = r"snapshot=(\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2})"
    snapshot_blobs = [blob for blob in blobs if "snapshot=" in blob.name]

    if not snapshot_blobs:
        logger.error("No snapshot files found in the catalog")
        return

    # Find the latest snapshot
    latest_snapshot = max(
        re.search(snapshot_pattern, blob.name).group(1) for blob in snapshot_blobs
    )
    logger.info(f"Found latest snapshot: {latest_snapshot}")

    # Filter for only the latest snapshot
    blobs = [
        blob for blob in snapshot_blobs if f"snapshot={latest_snapshot}" in blob.name
    ]

    # Filter out files that already exist with matching size
    blobs_to_download = []
    for blob in blobs:
        local_path = os.path.join(download_path, blob.name)
        if os.path.exists(local_path):
            local_size = os.path.getsize(local_path)
            if local_size == blob.size:
                logger.debug(
                    f"Skipping {blob.name} - already exists with matching size"
                )
                continue
            else:
                logger.debug(
                    f"Re-downloading {blob.name} - size mismatch (local: {local_size}, remote: {blob.size})"
                )
        blobs_to_download.append(blob)

    total_size = sum(blob.size for blob in blobs_to_download)
    logger.info(
        f"Found {len(blobs_to_download)} files to download out of {len(blobs)} total. "
        f"Total download size: {total_size / (1024*1024):.2f} MB"
    )

    if not blobs_to_download:
        logger.info("All files are already downloaded and up to date!")
        return

    # Create a semaphore to limit concurrent downloads
    semaphore = asyncio.Semaphore(max_concurrent)

    # Create download tasks for each blob
    tasks = []
    for i, blob in enumerate(blobs_to_download):
        task = download_blob(blob, download_path, semaphore, i)
        tasks.append(task)

    # Run downloads concurrently
    await asyncio.gather(*tasks)


async def main() -> None:
    parser = argparse.ArgumentParser(description="Octogen Catalog Tools")
    parser.add_argument(
        "--catalog",
        type=str,
        help="Name of the catalog to download or print",
        required=True,
    )
    parser.add_argument(
        "--download",
        type=str,
        help="Path where catalog files will be downloaded",
        required=True,
    )
    args = parser.parse_args()

    if not load_dotenv():
        logger.error("Failed to load .env file")
        logger.error(
            "Please see README.md for more information on how to set up the .env file."
        )
        return
    octogen_catalog_bucket = os.getenv("OCTOGEN_CATALOG_BUCKET_NAME")
    octogen_customer_name = os.getenv("OCTOGEN_CUSTOMER_NAME")
    if not octogen_catalog_bucket or not octogen_customer_name:
        logger.error(
            "Please set OCTOGEN_CATALOG_BUCKET_NAME and OCTOGEN_CUSTOMER_NAME in the .env file."
        )
        logger.error(
            "Please see README.md for more information on how to set up the .env file."
        )
        return

    await download_catalog(
        octogen_catalog_bucket=octogen_catalog_bucket,
        octogen_customer_name=octogen_customer_name,
        catalog=args.catalog,
        download_path=args.download,
    )


if __name__ == "__main__":
    asyncio.run(main())
