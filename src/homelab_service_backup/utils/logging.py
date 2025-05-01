"""Logging utilities."""

import logging
import sys

from loguru import logger

from .config import Config
from .console import console


def cli_log_formatter(record: dict) -> str:
    """Format log messages with rich styling for CLI output.

    Apply color styling to log messages based on their level using rich markup syntax. Maps each log level to a specific color and formats the timestamp, level and message with consistent spacing.

    Args:
        record (dict): The log record containing level, message and other metadata.

    Returns:
        str: The formatted log message with rich markup for color styling.
    """
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

    return f"{{time:YYYY-MM-DD HH:mm}} | [{lvl_color}]{{level: <8}} | {{message}}[/{lvl_color}]"


def log_file_formatter(record: dict) -> str:
    """Format log messages for writing to log files with consistent structure and metadata.

    Replace rich markup syntax with plain text and combine timestamp, hostname, level and message into a standardized log line format.

    Args:
        record (dict): The log record containing message, level and other metadata.

    Returns:
        str: The formatted log line with timestamp, hostname, level and message.
    """
    message = record["message"].replace("[code]", "'").replace("[/]", "'")

    return f"{{time:YYYY-MM-DD HH:mm:ss}} | {Config().host_name: <7} | {{level: <7}} | {Config().job_name}: {message}\n"


def instantiate_logger() -> None:  # pragma: no cover
    """Configure and initialize the Loguru logger with console and file outputs.

    Set up console logging with color formatting and optional file logging with rotation. Configure the logger based on settings from Config() including log level, file path, and output destinations. Intercept and redirect standard logging to Loguru.
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
            enqueue=True,
        )

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
    def emit(record: logging.LogRecord) -> None:
        """Intercepts standard logging and redirects to Loguru.

        This method is called by the Python logging module when a logging message is emitted. It intercepts the message and redirects it to Loguru, a third-party logging library. The method determines the corresponding Loguru level for the message and logs it using the Loguru logger.

        Args:
            record: A logging.LogRecord object representing the logging message.
        """
        # Get corresponding Loguru level if it exists.
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno  # type: ignore [assignment]

        # Find caller from where originated the logged message.
        frame, depth = sys._getframe(6), 6  # noqa: SLF001
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back  # type: ignore [assignment]
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())
