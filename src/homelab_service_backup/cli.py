"""service-backup CLI."""

import datetime
import time

import inflect
import typer
from confz import validate_all_configs
from loguru import logger
from nclutils import print_debug
from pydantic import ValidationError

from homelab_service_backup.modules import (
    do_backup_filesystem,
    do_backup_postgres,
    do_restore_filesystem,
    do_restore_postgres,
    setup_schedule,
)
from homelab_service_backup.utils import Config, console, instantiate_logger

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    rich_markup_mode="rich",
    context_settings={"help_option_names": ["-h", "--help"]},
)
typer.rich_utils.STYLE_HELPTEXT = ""
p = inflect.engine()


def log_config_trace(config: Config) -> None:
    """Log configuration at TRACE level if enabled."""
    if config.log_level in {"TRACE", "DEBUG"}:
        print_debug(
            custom=[
                {"Config": config.model_dump()},
                {"System Time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")},  # noqa: DTZ005
            ],
            packages=["nclutils", "loguru", "sh", "typer", "rich", "confz", "apscheduler", "arrow"],
        )


@app.command()
def main() -> None:
    """Add application documentation here."""
    instantiate_logger()

    # Load and validate configuration
    try:
        validate_all_configs()
    except ValidationError as e:
        logger.error(f"Invalid environment variables: {e}")
        for error in e.errors():
            console.print(f"           [red]{error['loc'][0]}: {error['msg']}[/red]")
        raise typer.Exit(code=1) from e

    config = Config()

    log_config_trace(config)

    if config.schedule:
        setup_schedule()
        while True:  # Run the scheduler in a loop
            time.sleep(1)

    if not config.schedule and config.action == "backup":
        if config.use_postgres:
            logger.info("Backing up PostgreSQL database")
            do_backup_postgres()
        else:
            logger.info("Backing up filesystem")
            do_backup_filesystem()

    if not config.schedule and config.action == "restore":
        if config.use_postgres:
            logger.info("Restoring PostgreSQL database")
            do_restore_postgres()
        else:
            logger.info("Restoring filesystem")
            do_restore_filesystem()


if __name__ == "__main__":
    app()
