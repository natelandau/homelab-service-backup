"""Scheduler module for the backup service."""

import inflect
from apscheduler.schedulers.background import BackgroundScheduler
from loguru import logger

from homelab_service_backup.utils import Config

from .backup import do_backup
from .restore import do_restore

p = inflect.engine()


def setup_schedule() -> None:
    """Setup the scheduler for the backup or restore task."""
    scheduler = BackgroundScheduler()

    if Config().action == "backup":
        scheduler.add_job(
            do_backup,
            "cron",
            minute=Config().schedule_minute,
            hour=Config().schedule_hour,
            day_of_week=Config().schedule_day_of_week,
            week=Config().schedule_week,
            day=Config().schedule_day,
            jitter=600,
            timezone=Config().tz,
        )
        logger.success("Scheduled backup task")

    elif Config().action == "restore":
        scheduler.add_job(
            do_restore,
            "cron",
            minute=Config().schedule_minute,
            hour=Config().schedule_hour,
            day_of_week=Config().schedule_day_of_week,
            week=Config().schedule_week,
            day=Config().schedule_day,
            jitter=600,
            timezone=Config().tz,
        )
        logger.success("Scheduled restore task")
        logger.info(
            f"Schedule: minute: {Config().schedule_minute}, hour: {Config().schedule_hour}, day_of_week: {Config().schedule_day_of_week}, week: {Config().schedule_week}, day: {Config().schedule_day}"
        )

    # Start the scheduler
    scheduler.start()
