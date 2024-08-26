# type: ignore
"""Test helper utilities."""

from pathlib import Path

import pytest
from freezegun import freeze_time

from homelab_service_backup.constants import FILESYSTEM_BACKUP_EXT
from homelab_service_backup.utils.helpers import (
    Config,
    clean_directory,
    clean_old_backups,
    filter_file_for_backup,
    find_most_recent_backup,
    type_of_backup,
)


def test_clean_directory(tmp_path: Path):
    """Test that clean_directory successfully deletes all files and subdirectories, leaving the directory empty but intact."""
    # GIVEN: Pre-assertions to verify the setup of the test environment
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    (test_dir / "subdir").mkdir()
    (test_dir / "subdir" / "file.txt").touch()
    (test_dir / "subdir" / "subdir").mkdir()
    (test_dir / "subdir" / "subdir" / "file.txt").touch()
    (test_dir / "another_file.txt").touch()
    assert (test_dir / "subdir").exists()
    assert (test_dir / "subdir" / "file.txt").exists()
    assert (test_dir / "another_file.txt").exists()

    # WHEN: The clean_directory function is invoked
    clean_directory(test_dir)

    # THEN: The directory should be empty but still exist
    assert test_dir.exists(), "The directory itself should not be deleted."
    assert not list(test_dir.iterdir()), "The directory should be empty after cleaning."


def test_find_most_recent_backup(mock_config, backup_dir: Path, debug):
    """Test that find_most_recent_backup correctly identifies the most recent backup file."""
    # WHEN: Invoking the function to find the most recent backup
    with Config.change_config_sources(mock_config(backup_storage_dir=backup_dir)):
        most_recent_backup = find_most_recent_backup()
        # debug("config", Config().model_dump())

        # THEN: The function should return the path to the most recently modified backup file
        expected_backup_file = (
            backup_dir / f"{Config().job_name}-20220202T020200-yearly.{FILESYSTEM_BACKUP_EXT}"
        )

        assert (
            most_recent_backup == expected_backup_file
        ), "The function should identify the most recent backup file correctly."


@pytest.mark.parametrize(
    ("date", "expected"),
    [
        ("20220202", "hourly"),
        ("20230114", "daily"),
        ("20230101", "yearly"),
        ("20230201", "monthly"),
        ("20240325", "weekly"),
    ],
)
def test_backup_type_of_backup(backup_dir: Path, mock_config, date: str, expected: str):
    """Test BackupService.type_of_backup."""
    with Config.change_config_sources(mock_config(backup_storage_dir=backup_dir)):
        freezer = freeze_time(date)
        freezer.start()
        assert type_of_backup() == expected
        freezer.stop()


def test_clean_old_backups(backup_dir: Path, mock_config, debug) -> None:
    """Test cleaning old backups."""
    with Config.change_config_sources(mock_config(backup_storage_dir=backup_dir)):
        deleted_files = clean_old_backups()

        # debug("config", Config().model_dump())
        # debug("dir", backup_dir)

    assert len(deleted_files) == 5
    deleted_filenames = [str(x.relative_to(backup_dir)) for x in deleted_files]
    assert deleted_filenames == [
        "test_job-20210101T010100-hourly.tgz",
        "test_job-20210101T010100-daily.tgz",
        "test_job-20210101T010100-weekly.tgz",
        "test_job-20210101T010100-monthly.tgz",
        "test_job-20210101T010100-yearly.tgz",
    ]


@pytest.mark.parametrize(
    ("filename", "config", "expected"),
    [
        ("foo.txt", {}, True),
        ("foo.txt", {"include_files": "bar.txt,baz.txt"}, False),
        ("foo.txt", {"include_files": "foo.txt"}, True),
        ("foo.txt", {"include_regex": r".*\.md"}, False),
        ("foo.txt", {"include_regex": r".*\.txt"}, True),
        ("foo.txt", {"exclude_files": "bar.txt,baz.txt"}, True),
        ("foo.txt", {"exclude_files": "foo.txt"}, False),
        ("foo.txt", {"exclude_regex": r".*\.md"}, True),
        ("foo.txt", {"exclude_regex": r".*\.txt"}, False),
    ],
)
def test_filter_file_for_backup(mock_config, filename: str, config: dict, expected: bool, debug):
    """Test filter_file_for_backup."""
    with Config.change_config_sources(mock_config(**config)):
        # debug("config", Config().model_dump())
        assert filter_file_for_backup(Path(filename)) == expected
