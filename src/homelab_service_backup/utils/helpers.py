"""Helper utilities for service_backup."""

import shutil
from pathlib import Path

import arrow
from arrow import Arrow
from loguru import logger

from homelab_service_backup.constants import BACKUP_EXT

from .config import Config


def clean_directory(directory: Path) -> None:
    """Recursively cleans up a directory, deleting all files and subdirectories.

    Args:
        directory (Path): The directory to clean up.
    """
    for child in directory.iterdir():
        if child.is_file():
            child.unlink()
        else:
            shutil.rmtree(child)

    logger.info(f"Deleted all files in {directory}")


def clean_old_backups() -> list[Path]:
    """Cleans up old database backups exceeding retention policies.

    Iterates over the backup files stored in the backup directory, organizing them by type
    (daily, weekly, monthly, yearly), and deletes files exceeding the retention count set for each
    type. It logs the action taken for each deleted backup.

    Returns:
        A list of Path objects representing the backup files that were deleted.
    """
    logger.debug("Check for old db backups to purge")
    deleted = 0
    backups: dict[str, list[Path]] = {
        "hourly": [],
        "daily": [],
        "weekly": [],
        "monthly": [],
        "yearly": [],
    }

    # Build the dictionary of backups
    backup_dir = Config().backup_storage_dir
    job_name = Config().job_name
    for file in sorted(
        backup_dir.glob(f"{job_name}-*.{BACKUP_EXT}"),
        key=lambda x: x.stat().st_mtime,
        reverse=True,
    ):
        for backup_type in backups:
            if file.name and backup_type in file.name:
                backups[backup_type].append(file)

    # # Now delete the old backups
    deleted_files = []
    for backup_type in backups:
        policy = getattr(Config(), f"retention_{backup_type}", 2)
        if len(backups[backup_type]) > policy:
            for backup in backups[backup_type][policy:]:
                logger.debug(f"Delete {backup.name}")
                deleted_files.append(backup)
                backup.unlink()
                deleted += 1

    return deleted_files


def get_current_time() -> Arrow:
    """Retrieves the current time, optionally adjusted to a specific timezone.

    Returns the current time as an Arrow object. If a timezone is specified in the application's
    configuration, adjusts the time to that timezone; otherwise, uses UTC.

    Returns:
        The current time as an Arrow object, possibly adjusted for timezone.
    """
    return arrow.utcnow().to(Config().tz)


def find_most_recent_backup() -> Path | None:
    """Finds the most recent backup for a specific job."""
    job_name = Config().job_name
    backup_dir = Config().backup_storage_dir
    backup_files = sorted(
        backup_dir.glob(f"{job_name}-*.{BACKUP_EXT}"), key=lambda x: x.stat().st_mtime
    )

    return backup_files[-1] if backup_files else None


def type_of_backup() -> str:
    """Determines the backup type based on the current date.

    Evaluates the current date to decide whether the backup should be classified as yearly,
    monthly, weekly, or daily.

    Returns:
        A string representing the backup type ('yearly', 'monthly', 'weekly', 'daily').
    """
    now = get_current_time()

    today = now.format("YYYY-MM-DD")
    yearly = now.span("year")[0].format("YYYY-MM-DD")
    monthly = now.span("month")[0].format("YYYY-MM-DD")

    most_recent = find_most_recent_backup()

    if most_recent and now.format("YYYYMMDD") in most_recent.name:
        return "hourly"

    if today == yearly:
        return "yearly"

    if today == monthly:
        return "monthly"

    if now.weekday() == 0:  # Monday is denoted by 0
        return "weekly"

    return "daily"
