"""Constants for service-backup."""

from pathlib import Path

import typer

APP_DIR = Path(typer.get_app_dir("service-backup"))
VERSION = "0.0.0"
BACKUP_EXT = "tgz"
ALWAYS_ECLUDE_FILENAMES = (".DS_Store", "@eaDir", ".Trashes", "__pycache__")
