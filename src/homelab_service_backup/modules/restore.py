"""Restore service data."""

import tarfile

from loguru import logger

from homelab_service_backup.utils import Config, find_most_recent_backup


def do_restore() -> bool:
    """Restore service data."""
    most_recent_backup = find_most_recent_backup()

    if not most_recent_backup:
        logger.error(f"No backups found to restore for {Config().job_name}")
        return False
    logger.debug(f"Restore from: {most_recent_backup}")

    destination = f"{Config().job_data_dir}"

    try:
        archive = tarfile.open(most_recent_backup)
        archive.extractall(path=destination, filter="data")
        archive.close()
    except tarfile.TarError as e:
        logger.error(f"Failed to restore backup: {e}")
        return False

    logger.success(f"Backup restored to {destination}")
    return True
