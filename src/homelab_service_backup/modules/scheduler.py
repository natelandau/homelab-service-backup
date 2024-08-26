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

    if Config().action == "backup" and not Config().use_postgres:
        scheduler.add_job(
            do_backup_filesystem,
            "cron",
            minute=Config().schedule_minute,
            hour=Config().schedule_hour,
            day_of_week=Config().schedule_day_of_week,
            week=Config().schedule_week,
            day=Config().schedule_day,
            jitter=600,
            timezone=Config().tz,
        )
        logger.success("Scheduled filesystem backup task")

    if Config().action == "backup" and Config().use_postgres:
        scheduler.add_job(
            do_backup_postgres,
            "cron",
            minute=Config().schedule_minute,
            hour=Config().schedule_hour,
            day_of_week=Config().schedule_day_of_week,
            week=Config().schedule_week,
            day=Config().schedule_day,
            jitter=600,
            timezone=Config().tz,
        )
        logger.success("Scheduled postgres backup task")

    if Config().action == "restore" and not Config().use_postgres:
        scheduler.add_job(
            do_restore_filesystem,
            "cron",
            minute=Config().schedule_minute,
            hour=Config().schedule_hour,
            day_of_week=Config().schedule_day_of_week,
            week=Config().schedule_week,
            day=Config().schedule_day,
            jitter=600,
            timezone=Config().tz,
        )
        logger.success("Scheduled filesystem restore task")

    if Config().action == "restore" and Config().use_postgres:
        scheduler.add_job(
            do_restore_postgres,
            "cron",
            minute=Config().schedule_minute,
            hour=Config().schedule_hour,
            day_of_week=Config().schedule_day_of_week,
            week=Config().schedule_week,
            day=Config().schedule_day,
            jitter=600,
            timezone=Config().tz,
        )
        logger.success("Scheduled postgres restore task")

    # Start the scheduler
    scheduler.start()
