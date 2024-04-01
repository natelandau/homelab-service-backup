"""Restore service data."""

import tarfile
import time

from loguru import logger

from homelab_service_backup.utils import Config, clean_directory, find_most_recent_backup


def do_restore() -> bool:
    """Restore service data."""
    # Confirm destination is empty
    clean_directory(Config().job_data_dir)

    most_recent_backup = find_most_recent_backup()

    if not most_recent_backup:
        logger.error(f"No backups found to restore for {Config().job_name}")
        return False
    logger.debug(f"Restore from: {most_recent_backup.name}")

    destination = f"{Config().job_data_dir}"

    try:
        archive = tarfile.open(most_recent_backup)
        archive.extractall(path=destination, filter="data")
        archive.close()
    except tarfile.TarError as e:
        logger.error(f"Failed to restore backup: {e}")
        return False

    time.sleep(5)
    logger.success(f"Data restored from {most_recent_backup.name}")

    return True
