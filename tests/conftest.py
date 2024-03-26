# type: ignore
"""Shared fixtures for tests."""

import os
from pathlib import Path

import pytest
from confz import DataSource, FileSource

from homelab_service_backup.constants import BACKUP_EXT
from homelab_service_backup.utils import Config, console


@pytest.fixture()
def backup_dir(tmp_path: Path, mock_config) -> Path:
    """Fixture to create a temporary backup directory with mock backup files, each having different modification times."""
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()

    with Config.change_config_sources(mock_config(backup_storage_dir=backup_dir)):
        # create daily backups
        # for i in range(8):
        #     backup_file = backup_dir / f"{Config().job_name}-2024032{i}T000{i}00-daily.{BACKUP_EXT}"
        #     backup_file.touch()
        #     # Set the file's modification time to a different value for each file
        #     if i == 1:
        #         os.utime(
        #             backup_file, (backup_file.stat().st_atime, backup_file.stat().st_mtime + i * 10)
        #         )

        # Create annual backups
        for x in ("hourly", "daily", "weekly", "monthly", "yearly"):
            for i in range(2):
                n = i + 1
                backup_file = (
                    backup_dir / f"{Config().job_name}-202{n}0{n}0{n}T0{n}0{n}00-{x}.{BACKUP_EXT}"
                )
                backup_file.touch()
                if i == 1 and x == "yearly":
                    os.utime(
                        backup_file,
                        (backup_file.stat().st_atime, backup_file.stat().st_mtime + i * 100),
                    )
                elif i == 1:
                    os.utime(
                        backup_file,
                        (backup_file.stat().st_atime, backup_file.stat().st_mtime + i * 10),
                    )

        return backup_dir


@pytest.fixture()
def debug():
    """Print debug information to the console. This is used to debug tests while writing them."""

    def _debug_inner(label: str, value: str | Path, breakpoint: bool = False, width: int = 80):
        """Print debug information to the console. This is used to debug tests while writing them.

        Args:
            label (str): The label to print above the debug information.
            value (str | Path): The value to print. When this is a path, prints all files in the path.
            breakpoint (bool, optional): Whether to break after printing. Defaults to False.
            width (int, optional): The width of the console output. Defaults to 80, pytest's default when running without `-s`.

        Returns:
            bool: Whether to break after printing.
        """
        console.rule(label)

        # If a directory is passed, print the contents
        if isinstance(value, Path) and value.is_dir():
            for p in value.rglob("*"):
                console.print(p, width=width)
        else:
            console.print(value, width=width)

        console.rule()

        if breakpoint:
            return pytest.fail("Breakpoint")

        return True

    return _debug_inner


@pytest.fixture()
def mock_config():
    """Mock specific configuration data for use in tests by accepting arbitrary keyword arguments.

    The function dynamically collects provided keyword arguments, filters out any that are None,
    and prepares data sources with the overridden configuration for file processing.

    Usage:
        def test_something(mock_config):
            # Override the configuration with specific values
            with Config.change_config_sources(mock_config(some_key="some_value")):
                    # Test the functionality
                    result = do_something()
                    assert result
    """

    def _inner(**kwargs):
        """Collects provided keyword arguments, omitting any that are None, and prepares data sources with the overridden configuration.

        Args:
            **kwargs: Arbitrary keyword arguments representing configuration settings.

        Returns:
            list: A list containing a FileSource initialized with the fixture configuration and a DataSource with the overridden data.
        """
        # Filter out None values from kwargs
        override_data = {key: value for key, value in kwargs.items() if value is not None}

        # Define the path to the fixture configuration file
        fixture_config = Path(__file__).resolve().parent / "fixtures/fixture_config.toml"

        # Return a list of data sources with the overridden configuration
        return [FileSource(fixture_config), DataSource(data=override_data)]

    return _inner
