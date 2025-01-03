"""Helper utilities for service_backup."""

import os
import re
import shutil
from pathlib import Path

import arrow
import inflect
from arrow import Arrow
from loguru import logger

from homelab_service_backup.constants import FILESYSTEM_BACKUP_EXT, POSTGRES_BACKUP_EXT

from .config import Config

p = inflect.engine()


def get_job_name() -> str:
    """Retrieve the name of the current job. If backup type is postgres, append '-postgres' to the job name.

    Returns:
        str: The name of the current job.
    """
    if Config().use_postgres:
        return f"{Config().job_name}-postgres"

    return Config().job_name


def get_backup_file_extension() -> str:
    """Retrieve the file extension for the current backup type.

    Returns:
        str: The file extension for the current backup type.
    """
    if Config().use_postgres:
        return POSTGRES_BACKUP_EXT

    return FILESYSTEM_BACKUP_EXT


def chown_all_files(directory: Path | str) -> None:
    """Recursively change the ownership of all files in a directory.

    Args:
        directory (Path | str): The directory to recursively change the ownership of.
    """
    if isinstance(directory, str):
        directory = Path(directory)

    config = Config()
    if not config.chown_user or not config.chown_group:
        logger.debug("No chown_user or chown_group specified in config")
        return

    uid = int(config.chown_user)
    gid = int(config.chown_group)
    # Find all files using pathlib and chown the owner and group

    os.chown(directory.resolve(), uid, gid)

    for file in directory.rglob("*"):
        try:
            os.chown(file.resolve(), uid, gid)
        except OSError as e:
            logger.error(f"Failed to chown {file}: {e}")

    logger.info(f"Changed ownership of all files in {directory} to {uid}:{gid}")


def filter_file_for_backup(file: Path) -> bool:
    """Determine whether a file should be backed up based on inclusion and exclusion criteria.

    This function decides if a given file should be included in a backup operation. It evaluates
    the file against a set of inclusion and exclusion rules defined in the application's configuration.
    A file must meet any specified inclusion criteria and not meet any of the exclusion criteria to be
    eligible for backup. The rules can be specified as exact file paths or regular expressions.

    Args:
        file (Path): The file path to evaluate for backup eligibility.

    Returns:
        bool: True if the file should be backed up, based on the evaluation of inclusion and
              exclusion rules. False otherwise.
    """
    config = Config()
    include_files = config.include_files
    exclude_files = config.exclude_files
    include_regex = re.compile(config.include_regex) if config.include_regex else None
    exclude_regex = re.compile(config.exclude_regex) if config.exclude_regex else None

    test_path = str(file)

    # Skip files that don't match the include rules
    if include_files and test_path not in include_files:
        logger.trace(f"Skipping file due to include rules: {file}")
        return False
    if include_regex and not include_regex.match(test_path):
        logger.trace(f"Skipping file due to include regex: {file}")
        return False

    # Skip files that match the exclude rules
    if exclude_files and test_path in exclude_files:
        logger.trace(f"Skipping file due to exclude rules: {file}")
        return False
    if exclude_regex and exclude_regex.match(test_path):
        logger.trace(f"Skipping file due to exclude regex: {file}")
        return False

    return True


def clean_directory(directory: Path) -> None:
    """Recursively cleans up a directory, deleting all files and subdirectories.

    Args:
        directory (Path): The directory to clean up.
    """
    if not directory.is_dir():
        logger.warning(f"{directory} is not a directory. Can not clean up.")
        return

    n = 0
    for child in directory.iterdir():
        n += 1
        if child.is_file():
            child.unlink()
        else:
            shutil.rmtree(child)

    if n == 0:
        logger.debug(f"{directory} is already empty")
    else:
        logger.info(f"Deleted {n} {p.plural_noun('file', n)} in {directory}")


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
    job_name = get_job_name()
    for file in sorted(
        backup_dir.glob(f"{job_name}-*.{get_backup_file_extension()}"),
        key=lambda x: x.stat().st_mtime,
        reverse=True,
    ):
        for backup_type in backups:  # noqa: PLC0206
            if file.name and backup_type in file.name:
                backups[backup_type].append(file)

    # # Now delete the old backups
    deleted_files = []
    for backup_type in backups:  # noqa: PLC0206
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
    job_name = get_job_name()
    backup_dir = Config().backup_storage_dir
    backup_files = sorted(
        backup_dir.glob(f"{job_name}-*.{get_backup_file_extension()}"),
        key=lambda x: x.stat().st_mtime,
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
