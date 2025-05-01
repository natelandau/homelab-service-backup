"""Restore service data."""

import gzip
import os
import tarfile
import time
from pathlib import Path

import typer
from loguru import logger
from sh import ErrorReturnCode, psql

from homelab_service_backup.utils import (
    Config,
    chown_all_files,
    clean_directory,
    find_most_recent_backup,
    get_job_name,
)


def do_restore_postgres() -> bool:
    """Restore a PostgreSQL database from the most recent backup file.

    Find and decompress the most recent backup file, then restore it to the configured PostgreSQL database using psql. The backup must be a gzipped SQL dump created by pg_dump.

    Returns:
        bool: True if restore succeeds, False if no backups found.

    Raises:
        typer.Exit: If psql fails to restore the backup
    """
    most_recent_backup = find_most_recent_backup()
    if not most_recent_backup:
        logger.error(f"No backups found to restore for {get_job_name()}")
        return False
    logger.debug(f"Restore from: {most_recent_backup.name}")

    # Set password in PGPASSWORD environment variable
    os.environ["PGPASSWORD"] = Config().postgres_password

    with gzip.open(most_recent_backup, "rb") as f:
        file_content = f.read()

    try:
        psql(
            "-h",
            Config().postgres_host,
            "-p",
            Config().postgres_port,
            "-U",
            Config().postgres_user,
            "-d",
            Config().postgres_db,
            # "-f",
            # most_recent_backup,
            _in=file_content,
        )
    except ErrorReturnCode as e:
        msg = e.stderr.decode("utf-8").strip()
        logger.error(msg)
        raise typer.Exit(code=1) from e

    logger.success(f"Data restored from {most_recent_backup.name}")
    return True


def do_restore_filesystem() -> bool:
    """Extract and restore service data from the most recent backup archive.

    Find the most recent backup archive, clean the destination directory, and extract the archive contents. After extraction, update file ownership permissions.

    Returns:
        bool: True if restore succeeds, False if no backups found or extraction fails.

    Raises:
        typer.Exit: If no job data directory is configured
    """
    if Config().job_data_dir == Path("/nonexistent"):
        logger.error("No job data directory specified")
        raise typer.Exit(code=1)

    # Confirm destination is empty
    clean_directory(Config().job_data_dir)

    most_recent_backup = find_most_recent_backup()

    if not most_recent_backup:
        logger.error(f"No backups found to restore for {get_job_name()}")
        return False
    logger.debug(f"Restore from: {most_recent_backup.name}")

    destination = f"{Config().job_data_dir}"

    try:
        with tarfile.open(most_recent_backup) as archive:
            archive.extractall(path=destination, filter="data")
    except tarfile.TarError as e:
        logger.error(f"Failed to restore backup: {e}")
        return False

    time.sleep(5)
    chown_all_files(destination)

    logger.success(f"Data restored from {most_recent_backup.name}")

    return True
