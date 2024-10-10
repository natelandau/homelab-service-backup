"""Backup service data."""

import os
import tarfile
from pathlib import Path

import inflect
import typer
from loguru import logger
from sh import ErrorReturnCode, pg_dump

from homelab_service_backup.constants import ALWAYS_ECLUDE_FILENAMES
from homelab_service_backup.utils import (
    Config,
    clean_directory,
    clean_old_backups,
    filter_file_for_backup,
    get_backup_file_extension,
    get_current_time,
    get_job_name,
    type_of_backup,
)

p = inflect.engine()


def do_backup_postgres() -> Path | None:
    """Backup a PostgreSQL database."""
    logger.debug("Begin backup PostgreSQL database")

    backup_dir = Config().backup_storage_dir
    backup_type = type_of_backup()
    job_name = get_job_name()
    timestamp = get_current_time().format("YYYYMMDDTHHmmss")
    backup_filename = f"{job_name}-{timestamp}-{backup_type}.{get_backup_file_extension()}"
    backup_file = backup_dir / backup_filename
    logger.trace(f"{backup_file=!s}")

    # Set password in PGPASSWORD environment variable
    os.environ["PGPASSWORD"] = Config().postgres_password

    try:
        pg_dump(
            "-h",
            Config().postgres_host,
            "-p",
            Config().postgres_port,
            "-U",
            Config().postgres_user,
            "-d",
            Config().postgres_db,
            "--clean",
            "--if-exists",
            "-Z",
            "9",
            _out=backup_file,
        )
    except ErrorReturnCode as e:
        if backup_file.exists():
            logger.debug("Removing incomplete backup file")
            backup_file.unlink()
        msg = e.stderr.decode("utf-8").strip()
        logger.error(msg)
        raise typer.Exit(code=1) from e

    logger.success(f"Backup created: {backup_file.name}")

    deleted_backups = clean_old_backups()
    if deleted_backups:
        logger.info(
            f"Delete {len(deleted_backups)} old {p.plural_noun('backup', len(deleted_backups))}"
        )

    if Config().delete_source and Config().job_data_dir != Path("/nonexistent"):
        clean_directory(Config().job_data_dir)

    return backup_file


def do_backup_filesystem() -> Path | None:
    """Backup service data."""
    if Config().job_data_dir == Path("/nonexistent"):
        logger.error("No job data directory specified")
        raise typer.Exit(code=1)

    logger.debug(f"Begin backup source directory: {Config().job_data_dir}")

    source_dir = Config().job_data_dir
    backup_dir = Config().backup_storage_dir
    backup_type = type_of_backup()
    job_name = get_job_name()
    timestamp = get_current_time().format("YYYYMMDDTHHmmss")
    backup_filename = f"{job_name}-{timestamp}-{backup_type}.{get_backup_file_extension()}"
    backup_file = backup_dir / backup_filename
    logger.trace(f"{backup_file=!s}")

    # NOTE: compresslevel 6 is the tar program default
    try:
        with tarfile.open(backup_file, "w:gz", compresslevel=9) as tar:
            for file in source_dir.rglob("*"):
                f = file.relative_to(source_dir)

                # Skip files that should always be excluded
                if f.name in ALWAYS_ECLUDE_FILENAMES:
                    continue

                # Respect include/exclude rules
                if filter_file_for_backup(f):
                    logger.debug(f"-> '{f}'")
                    tar.add(file, arcname=f)
    except tarfile.TarError as e:
        logger.error(f"Failed to create backup: {e}")
        return None

    logger.success(f"Backup created: {backup_file.name}")

    deleted_backups = clean_old_backups()
    if deleted_backups:
        logger.info(
            f"Delete {len(deleted_backups)} old {p.plural_noun('backup', len(deleted_backups))}"
        )

    if Config().delete_source:
        clean_directory(Config().job_data_dir)

    return backup_file
