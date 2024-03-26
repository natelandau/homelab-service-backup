"""Instantiate Config class and set default values."""

from pathlib import Path
from typing import ClassVar, Literal, Optional

from confz import BaseConfig, ConfigSources, EnvSource
from pydantic import validator


class Config(BaseConfig):  # type: ignore [misc]
    """service-backup Configuration."""

    # Default values
    action: Literal["backup", "restore"]
    backup_storage_dir: Path
    delete_source: bool = False
    host_name: str = "unknown"
    job_data_dir: Path
    job_name: str
    log_file: str = "homelab_service_backup.log"
    log_level: str = "INFO"  # TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL
    log_to_file: bool = True
    retention_daily: int = 6
    retention_hourly: int = 2
    retention_monthly: int = 2
    retention_weekly: int = 3
    retention_yearly: int = 2
    schedule_day_of_week: Optional[str] = None
    schedule_day: Optional[str] = None
    schedule_hour: Optional[str] = None
    schedule_minute: Optional[str] = None
    schedule_week: Optional[str] = None
    schedule: bool = False
    specific_files: Optional[tuple[str, ...]] = None
    exclude_files: Optional[tuple[str, ...]] = None
    tz: str = "Etc/UTC"

    CONFIG_SOURCES: ClassVar[ConfigSources | None] = EnvSource(
        file=".env",  # Default file to read from
        allow=[
            "HSB_ACTION",
            "HSB_BACKUP_STORAGE_DIR",
            "HSB_DELETE_SOURCE",
            "HSB_HOST_NAME",
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
            "HSB_SPECIFIC_FILES",
            "HSB_EXCLUDE_FILES",
            "HSB_TZ",
        ],
        remap={
            "HSB_ACTION": "action",
            "HSB_BACKUP_STORAGE_DIR": "backup_storage_dir",
            "HSB_DELETE_SOURCE": "delete_source",
            "HSB_HOST_NAME": "host_name",
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
            "HSB_SPECIFIC_FILES": "specific_files",
            "HSB_TZ": "tz",
            "HSB_EXCLUDE_FILES": "exclude_files",
        },
    )

    @validator("specific_files", "exclude_files", pre=True, each_item=False)
    def split_string(cls, v: str) -> tuple[str, ...]:
        """Split a string into a tuple of strings."""
        return tuple(v.split(","))

    @validator("backup_storage_dir", "job_data_dir", pre=True)
    def validate_path(cls, string: str) -> Path:
        """Validates a string as a valid path.

        Args:
            string (str): The string to validate.

        Returns:
            Path: The validated path.
        """
        path = Path(string).resolve()
        if not path.exists():
            msg = f"Path does not exist: {path}"
            raise ValueError(msg)
        return path
