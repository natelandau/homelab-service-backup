"""Duty tasks for the project."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from textwrap import dedent
from typing import TYPE_CHECKING

from duty import duty, tools
from nclutils import console

if TYPE_CHECKING:
    from duty.context import Context

PY_SRC_PATHS = (Path(_) for _ in ("src/", "tests/", "duties.py", "scripts/") if Path(_).exists())
PY_SRC_LIST = tuple(str(_) for _ in PY_SRC_PATHS)
CI = os.environ.get("CI", "0") in {"1", "true", "yes", ""}


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from a string.

    Args:
        text (str): String to remove ANSI escape sequences from.

    Returns:
        str: String without ANSI escape sequences.
    """
    ansi_chars = re.compile(r"(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]")

    # Replace [ with \[ so rich doesn't interpret output as style tags
    return ansi_chars.sub("", text).replace("[", r"\[")


def pyprefix(title: str) -> str:
    """Add a prefix to the title if CI is true.

    Returns:
        str: Title with prefix if CI is true.
    """
    if CI:
        prefix = f"(python{sys.version_info.major}.{sys.version_info.minor})"
        return f"{prefix:14}{title}"
    return title


@duty(silent=True)
def clean(ctx: Context) -> None:
    """Clean the project."""
    ctx.run("rm -rf .cache")
    ctx.run("rm -rf build")
    ctx.run("rm -rf dist")
    ctx.run("rm -rf pip-wheel-metadata")
    ctx.run("find . -type d -name __pycache__ | xargs rm -rf")
    ctx.run("find . -name '.DS_Store' -delete")


@duty
def ruff(ctx: Context) -> None:
    """Check the code quality with ruff."""
    ctx.run(
        tools.ruff.check(*PY_SRC_LIST, fix=False, config="pyproject.toml"),
        title=pyprefix("code quality check"),
        command="ruff check --config pyproject.toml --no-fix src/",
    )


@duty
def format(ctx: Context) -> None:  # noqa: A001
    """Format the code with ruff."""
    ctx.run(
        tools.ruff.format(*PY_SRC_LIST, check=True, config="pyproject.toml"),
        title=pyprefix("code formatting"),
        command="ruff format --check --config pyproject.toml src/",
    )


@duty
def mypy(ctx: Context) -> None:
    """Check the code with mypy."""
    os.environ["FORCE_COLOR"] = "1"
    ctx.run(
        tools.mypy("src/", config_file="pyproject.toml"),
        title=pyprefix("mypy check"),
        command="mypy --config-file pyproject.toml src/",
    )


@duty
def typos(ctx: Context) -> None:
    """Check the code with typos."""
    ctx.run(
        ["typos", "--config", ".typos.toml"],
        title=pyprefix("typos check"),
        command="typos --config .typos.toml",
    )


@duty(skip_if=CI, skip_reason="skip pre-commit in CI environments")
def precommit(ctx: Context) -> None:
    """Run pre-commit hooks."""
    ctx.run(
        "SKIP=mypy,pytest,ruff pre-commit run --all-files",
        title=pyprefix("pre-commit hooks"),
    )


@duty(pre=[ruff, mypy, typos, precommit], capture=CI)
def lint(ctx: Context) -> None:
    """Run all linting duties."""


@duty(capture=False)
def update(ctx: Context) -> None:
    """Update the project."""
    ctx.run(["uv", "lock", "--upgrade"], title="update uv lock")
    ctx.run(["pre-commit", "autoupdate"], title="pre-commit autoupdate", capture=CI)


@duty()
def test(ctx: Context, *cli_args: str) -> None:
    """Test package and generate coverage reports."""
    ctx.run(
        tools.pytest(
            "tests",
            config_file="pyproject.toml",
            color="yes",
        ).add_args(
            "--cov",
            "--cov-config=pyproject.toml",
            "--cov-report=xml",
            "--cov-report=term",
            *cli_args,
        ),
        title=pyprefix("Running tests"),
        capture=CI,
    )


@duty()
def dev_clean(ctx: Context) -> None:
    """Clean the development environment."""
    # We import these here to avoid importing code before pytest-cov is initialized
    from homelab_service_backup.constants import DEV_DIR  # noqa: PLC0415

    if DEV_DIR.exists():
        ctx.run(["rm", "-rf", str(DEV_DIR)])


@duty(pre=[dev_clean])
def dev_setup(ctx: Context) -> None:
    """Provision a mock development environment."""
    # We import these here to avoid importing code before pytest-cov is initialized
    from homelab_service_backup.constants import DEV_DIR  # noqa: PLC0415

    project_1 = DEV_DIR / "files" / "project1"
    project_2 = DEV_DIR / "files" / "project2"

    directories = [
        project_1 / "somdir",
        project_2,
        DEV_DIR / "backups",
        DEV_DIR / "logs",
    ]
    for directory in directories:
        if not directory.exists():
            console.print(f"Create: {directory}")
            directory.mkdir(parents=True)

    # Create files
    files = [
        project_1 / "foo.txt",
        project_1 / "bar.txt",
        project_1 / "baz.txt",
        project_1 / "somdir" / "foo.txt",
        project_1 / "somdir" / "bar.txt",
        project_1 / "somdir" / "baz.txt",
        project_2 / "foo.txt",
        project_2 / "bar.txt",
        project_2 / "baz.txt",
    ]
    for file in files:
        if not file.exists():
            console.print(f"Create: {file}")
            file.touch()

    compose_file = DEV_DIR / "docker-compose.yml"
    if not compose_file.exists():
        console.print(f"Create: {compose_file}")
        compose_file.write_text(
            dedent(
                f"""
            name: test
            services:
              test:
                image: python:3.10
                build:
                    context: {compose_file.parent.parent}
                    dockerfile: Dockerfile
                container_name: test
                environment:
                    - HSB_ACTION=backup # backup or restore
                    - HSB_BACKUP_STORAGE_DIR=/backups
                    - HSB_JOB_NAME=test
                    - HSB_JOB_DATA_DIR=/files
                    - HSB_LOG_FILE=/logs/backup.log
                    - HSB_LOG_LEVEL=DEBUG # TRACE, DEBUG, INFO, SUCCESS, WARN, ERROR
                    - HSB_LOG_TO_FILE=true # true or false
                    - HSB_DELETE_SOURCE=false # false or true
                    - HSB_TZ=America/New_York
                    - TZ=America/New_York
                    - HSB_RETENTION_DAILY=6 # number of daily backups to keep
                    - HSB_RETENTION_HOURLY=2 # number of hourly backups to keep
                    - HSB_RETENTION_MONTHLY=11 # number of monthly backups to keep
                    - HSB_RETENTION_WEEKLY=3 # number of weekly backups to keep
                    - HSB_RETENTION_YEARLY=2 # number of yearly backups to keep
                    - HSB_SCHEDULE=true # true or false
                    - HSB_SCHEDULE_MINUTE=5 # minute<br>`*/12`, `1,10,16,23,45`
                    # - HSB_SCHEDULE_HOUR= # hour<br>`*/2`, `1,10,16,23`
                    # - HSB_SCHEDULE_DAY= # day of month<br>`3rd fri`, `1,21`, `last fr`
                    # - HSB_SCHEDULE_DAY_OF_WEEK= # number or name of weekday (Monday is 1)<br>`mon,fri`, `1-3`
                    # - HSB_SCHEDULE_WEEK= # ISO week (1-53)
                    # - HSB_EXCLUDE_FILES= # comma separated list of files or directories to exclude from the backup
                    # - HSB_EXCLUDE_REGEX= # regex pattern to exclude files or directories from the backup
                    # - HSB_INCLUDE_FILES= # comma separated list of specific files or directories to backup
                    # - HSB_INCLUDE_REGEX= # regex pattern to include files or directories in the backup
                volumes:
                    - ./files:/files
                    - ./backups:/backups
                    - ./logs:/logs
                develop:
                    watch:
                        - action: sync+restart
                          path: ../src/
                          target: /app/src/
                          ignore:
                            - .git/
                            - .github/
                            - .development/
                        - action: rebuild
                          path: ../uv.lock
                          target: /app/uv.lock
                        - action: rebuild
                          path: ../pyproject.toml
                          target: /app/pyproject.toml
                        - action: rebuild
                          path: ../Dockerfile
            """
            )
        )

    console.print(
        f"Development environment setup complete. Start the development environment with:\n\n    [code]docker compose -f {DEV_DIR.relative_to(Path.cwd())}/docker-compose.yml up --build[/code]"
    )
