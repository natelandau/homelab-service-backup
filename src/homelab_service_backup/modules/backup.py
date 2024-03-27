"""Backup service data."""

import tarfile
from pathlib import Path

import inflect
from loguru import logger

from homelab_service_backup.constants import ALWAYS_ECLUDE_FILENAMES
from homelab_service_backup.utils import (
    Config,
    clean_directory,
    clean_old_backups,
    filter_file_for_backup,
    get_current_time,
    type_of_backup,
)

p = inflect.engine()


def do_backup() -> Path | None:
    """Backup service data."""
    source_dir = Config().job_data_dir
    backup_dir = Config().backup_storage_dir
    backup_type = type_of_backup()
    job_name = Config().job_name
    timestamp = get_current_time().format("YYYYMMDDTHHmmss")
    backup_filename = f"{job_name}-{timestamp}-{backup_type}.tgz"
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
