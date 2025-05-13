"""Constants for service-backup."""

from pathlib import Path

import typer

APP_DIR = Path(typer.get_app_dir("service-backup"))
VERSION = "0.0.0"
FILESYSTEM_BACKUP_EXT = "tgz"
POSTGRES_BACKUP_EXT = "sql.gz"
ALWAYS_ECLUDE_FILENAMES = (".DS_Store", "@eaDir", ".Trashes", "__pycache__")
PROJECT_ROOT_PATH = Path(__file__).parents[2].absolute()
DEV_DIR = PROJECT_ROOT_PATH / ".development"
