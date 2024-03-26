"""Logging utilities."""

import logging
import sys

from loguru import logger

from .config import Config
from .console import console


def cli_log_formatter(record: dict) -> str:
    """Use rich to style log messages."""
    color_map = {
        "TRACE": "turquoise4",
        "DEBUG": "cyan",
        "INFO": "bold",
        "SUCCESS": "bold green",
        "WARNING": "bold yellow",
        "ERROR": "bold red",
        "CRITICAL": "bold white on red",
    }

    name = record["level"].name
    lvl_color = color_map.get(name, "bold")

    return f"[{lvl_color}]{{level: <8}} | {{message}}[/{lvl_color}]"


def log_file_formatter(record: dict) -> str:
    """Format log messages for log files."""
    message = record["message"].replace("[code]", "'").replace("[/]", "'")

    return f"{{time:YYYY-MM-DD HH:mm:ss}} |{Config().host_name: <4}| {{level: <7}} |{Config().job_name}: {message}\n"


def instantiate_logger() -> None:  # pragma: no cover
    """Instantiate the Loguru logger.

    Configure the logger with the specified verbosity level, log file path,
    and whether to log to a file.

    Returns:
        None
    """
    logger.remove()

    logger.add(
        console.print,
        level=Config().log_level.upper(),
        colorize=True,
        format=cli_log_formatter,  # type: ignore [arg-type]
    )

    if Config().log_to_file:
        logger.add(
            Config().log_file,
            level=Config().log_level.upper(),
            format=log_file_formatter,  # type: ignore [arg-type]
            rotation="50 MB",
            retention=2,
            compression="zip",
        )

    if Config().log_level.upper() not in {"TRACE", "DEBUG"}:
        # Intercept standard package logs and redirect to Loguru
        logging.getLogger("peewee").setLevel(level="DEBUG")
        logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)


class InterceptHandler(logging.Handler):  # pragma: no cover
    """Intercepts standard logging and redirects to Loguru.

    This class is a logging handler that intercepts standard logging messages and redirects them to Loguru, a third-party logging library. When a logging message is emitted, this handler determines the corresponding Loguru level for the message and logs it using the Loguru logger.

    Methods:
        emit: Intercepts standard logging and redirects to Loguru.

    Examples:
    To use the InterceptHandler with the Python logging module:
    ```
    import logging
    from logging import StreamHandler

    from loguru import logger

    # Create a new InterceptHandler and add it to the Python logging module.
    intercept_handler = InterceptHandler()
    logging.basicConfig(handlers=[StreamHandler(), intercept_handler], level=logging.INFO)

    # Log a message using the Python logging module.
    logging.info("This message will be intercepted by the InterceptHandler and logged using Loguru.")
    ```
    """

    @staticmethod
    def emit(record):  # type: ignore [no-untyped-def]
        """Intercepts standard logging and redirects to Loguru.

        This method is called by the Python logging module when a logging message is emitted. It intercepts the message and redirects it to Loguru, a third-party logging library. The method determines the corresponding Loguru level for the message and logs it using the Loguru logger.

        Args:
            record: A logging.LogRecord object representing the logging message.
        """
        # Get corresponding Loguru level if it exists.
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message.
        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())
