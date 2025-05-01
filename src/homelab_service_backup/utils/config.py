"""Instantiate Config class and set default values."""

from pathlib import Path
from typing import ClassVar, Literal

from confz import BaseConfig, ConfigSources, EnvSource
from pydantic import validator


class Config(BaseConfig):  # type: ignore [misc]
    """service-backup Configuration."""

    # Default values
    action: Literal["backup", "restore"]
    backup_storage_dir: Path
    chown_group: str | None = None
    chown_user: str | None = None
    delete_source: bool = False
    exclude_files: tuple[str, ...] = ()
    exclude_regex: str = ""
    host_name: str = "unknown"
    include_files: tuple[str, ...] = ()
    include_regex: str = ""
    job_data_dir: Path = Path("/nonexistent")
    job_name: str
    log_file: str = "homelab_service_backup.log"
    log_level: str = "INFO"  # TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL
    log_to_file: bool = True
    retention_daily: int = 6
    retention_hourly: int = 2
    retention_monthly: int = 2
    retention_weekly: int = 3
    retention_yearly: int = 2
    schedule_day_of_week: str | None = None
    schedule_day: str | None = None
    schedule_hour: str | None = None
    schedule_minute: str | None = None
    schedule_week: str | None = None
    schedule: bool = False
    tz: str = "Etc/UTC"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = ""
    postgres_password: str = ""
    postgres_db: str = ""
    use_postgres: bool = False

    CONFIG_SOURCES: ClassVar[ConfigSources | None] = EnvSource(
        file=".env",  # Default file to read from
        allow=[
            "HSB_ACTION",
            "HSB_BACKUP_STORAGE_DIR",
            "HSB_DELETE_SOURCE",
            "HSB_EXCLUDE_FILES",
            "HSB_EXCLUDE_REGEX",
            "HSB_HOST_NAME",
            "HSB_INCLUDE_FILES",
            "HSB_INCLUDE_REGEX",
            "HSB_JOB_DATA_DIR",
            "HSB_JOB_NAME",
            "HSB_LOG_FILE",
            "HSB_LOG_LEVEL",
            "HSB_LOG_TO_FILE",
            "HSB_RETENTION_DAILY",
            "HSB_RETENTION_HOURLY",
            "HSB_RETENTION_MONTHLY",
            "HSB_RETENTION_WEEKLY",
            "HSB_RETENTION_YEARLY",
            "HSB_SCHEDULE_DAY_OF_WEEK",
            "HSB_SCHEDULE_DAY",
            "HSB_SCHEDULE_HOUR",
            "HSB_SCHEDULE_MINUTE",
            "HSB_SCHEDULE_WEEK",
            "HSB_SCHEDULE",
            "HSB_TZ",
            "HSB_CHOWN_UID",
            "HSB_CHOWN_GID",
            "HSB_POSTGRES_HOST",
            "HSB_POSTGRES_PORT",
            "HSB_POSTGRES_USER",
            "HSB_POSTGRES_PASSWORD",
            "HSB_POSTGRES_DB",
            "HSB_USE_POSTGRES",
        ],
        remap={
            "HSB_ACTION": "action",
            "HSB_BACKUP_STORAGE_DIR": "backup_storage_dir",
            "HSB_DELETE_SOURCE": "delete_source",
            "HSB_EXCLUDE_FILES": "exclude_files",
            "HSB_EXCLUDE_REGEX": "exclude_regex",
            "HSB_HOST_NAME": "host_name",
            "HSB_INCLUDE_FILES": "include_files",
            "HSB_INCLUDE_REGEX": "include_regex",
            "HSB_JOB_DATA_DIR": "job_data_dir",
            "HSB_JOB_NAME": "job_name",
            "HSB_LOG_FILE": "log_file",
            "HSB_LOG_LEVEL": "log_level",
            "HSB_LOG_TO_FILE": "log_to_file",
            "HSB_RETENTION_DAILY": "retention_daily",
            "HSB_RETENTION_HOURLY": "retention_hourly",
            "HSB_RETENTION_MONTHLY": "retention_monthly",
            "HSB_RETENTION_WEEKLY": "retention_weekly",
            "HSB_RETENTION_YEARLY": "retention_yearly",
            "HSB_SCHEDULE_DAY_OF_WEEK": "schedule_day_of_week",
            "HSB_SCHEDULE_DAY": "schedule_day",
            "HSB_SCHEDULE_HOUR": "schedule_hour",
            "HSB_SCHEDULE_MINUTE": "schedule_minute",
            "HSB_SCHEDULE_WEEK": "schedule_week",
            "HSB_SCHEDULE": "schedule",
            "HSB_CHOWN_UID": "chown_user",
            "HSB_CHOWN_GID": "chown_group",
            "HSB_TZ": "tz",
            "HSB_POSTGRES_HOST": "postgres_host",
            "HSB_POSTGRES_PORT": "postgres_port",
            "HSB_POSTGRES_USER": "postgres_user",
            "HSB_POSTGRES_PASSWORD": "postgres_password",
            "HSB_POSTGRES_DB": "postgres_db",
            "HSB_USE_POSTGRES": "use_postgres",
        },
    )

    @validator("include_files", "exclude_files", pre=True, each_item=False)
    def split_string(cls, v: str) -> tuple[str, ...]:
        """Split a comma-separated string into a tuple of individual strings.

        Convert a comma-delimited string into a tuple of substrings by splitting on commas. Used for parsing configuration values that accept multiple items.

        Args:
            v (str): The comma-separated string to split.

        Returns:
            tuple[str, ...]: A tuple containing the individual strings after splitting.
        """
        if not v:
            return ()
        return tuple(v.split(","))

    @validator("backup_storage_dir", "job_data_dir", pre=True)
    def validate_path(cls, string: str) -> Path:
        """Convert a string to a Path object and verify it exists on the filesystem.

        Resolve the string to an absolute path and check that it exists. Useful for validating configuration paths.

        Args:
            string (str): The path string to validate and convert.

        Returns:
            Path: The resolved absolute Path object.

        Raises:
            ValueError: If the path does not exist on the filesystem.
        """
        path = Path(string).resolve()
        if not path.exists():
            msg = f"Path does not exist: {path}"
            raise ValueError(msg)
        return path
