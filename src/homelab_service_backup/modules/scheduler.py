"""Scheduler module for the backup service."""

import inflect
from apscheduler.schedulers.background import BackgroundScheduler
from loguru import logger

from homelab_service_backup.utils import Config

from .backup import do_backup_filesystem, do_backup_postgres
from .restore import do_restore_filesystem, do_restore_postgres

p = inflect.engine()


def setup_schedule() -> None:
    """Setup the scheduler for the backup or restore task."""
    scheduler = BackgroundScheduler()
    config = Config()

    if config.action == "backup" and not config.use_postgres:
        scheduler.add_job(
            do_backup_filesystem,
            "cron",
            minute=config.schedule_minute,
            hour=config.schedule_hour,
            day_of_week=config.schedule_day_of_week,
            week=config.schedule_week,
            day=config.schedule_day,
            jitter=600,
            timezone=config.tz,
        )
        logger.success("Scheduled filesystem backup task")

    if config.action == "backup" and config.use_postgres:
        scheduler.add_job(
            do_backup_postgres,
            "cron",
            minute=config.schedule_minute,
            hour=config.schedule_hour,
            day_of_week=config.schedule_day_of_week,
            week=config.schedule_week,
            day=config.schedule_day,
            jitter=600,
            timezone=config.tz,
        )
        logger.success("Scheduled postgres backup task")

    if config.action == "restore" and not config.use_postgres:
        scheduler.add_job(
            do_restore_filesystem,
            "cron",
            minute=config.schedule_minute,
            hour=config.schedule_hour,
            day_of_week=config.schedule_day_of_week,
            week=config.schedule_week,
            day=config.schedule_day,
            jitter=600,
            timezone=config.tz,
        )
        logger.success("Scheduled filesystem restore task")

    if config.action == "restore" and config.use_postgres:
        scheduler.add_job(
            do_restore_postgres,
            "cron",
            minute=config.schedule_minute,
            hour=config.schedule_hour,
            day_of_week=config.schedule_day_of_week,
            week=config.schedule_week,
            day=config.schedule_day,
            jitter=600,
            timezone=config.tz,
        )
        logger.success("Scheduled postgres restore task")

    logger.info(
        f"Schedule: minute: {config.schedule_minute}, hour: {config.schedule_hour}, day_of_week: {config.schedule_day_of_week}, week: {config.schedule_week}, day: {config.schedule_day}"
    )

    # Start the scheduler
    scheduler.start()
