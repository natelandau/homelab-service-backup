"""service-backup CLI."""

import time

import inflect
import typer
from confz import validate_all_configs
from loguru import logger
from pydantic import ValidationError

from homelab_service_backup.modules import do_backup, do_restore, setup_schedule
from homelab_service_backup.utils import Config, console, instantiate_logger

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    rich_markup_mode="rich",
    context_settings={"help_option_names": ["-h", "--help"]},
)
typer.rich_utils.STYLE_HELPTEXT = ""
p = inflect.engine()


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

    if Config().log_level == "TRACE":
        for k, v in Config().model_dump().items():
            logger.trace(f"{k}: {v}")

    if Config().schedule:
        setup_schedule()

        # Run the scheduler in a loop
        while True:
            time.sleep(1)

    if Config().action == "backup":
        do_backup()
    elif Config().action == "restore":
        do_restore()


if __name__ == "__main__":
    app()
