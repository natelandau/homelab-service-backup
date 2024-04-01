# homelab-service-backup

A Docker container to backup and restore data from services running in a homelab cluster orchestrated by Hashicorp Nomad. This container is designed to be run as a pre-start, post-star, and post-stop task along inside a Nomad job.

## Features

-   Backups are tar.gz compressed
-   Configurable retention policies
-   Dockerized for easy deployment
-   Scheduled backups

## Configuration

All configuration is managed through environment variables.

| Variable Name            | Required | Default     | Description                                                                               |
| ------------------------ | -------- | ----------- | ----------------------------------------------------------------------------------------- |
| HSB_ACTION               | ✅       |             | The action to take. `backup` or `restore`                                                 |
| HSB_BACKUP_STORAGE_DIR   | ✅       |             | The directory to store backups                                                            |
| HSB_CHOWN_GID            |          |             | If provided, change the group id that owns all files/dirs                                 |
| HSB_CHOWN_UID            |          |             | If provided, change the user id that owns all files/dirs                                  |
| HSB_DELETE_SOURCE        |          | `false`     | Delete all contents in the source directory after backup                                  |
| HSB_EXCLUDE_FILES        |          |             | A comma separated list of files or directories to exclude from the backup.                |
| HSB_EXCLUDE_REGEX        |          |             | A regex pattern to exclude files or directories from the backup.                          |
| HSB_HOST_NAME            |          | `localhost` | The hostname of the machine running the backup. Used in logs                              |
| HSB_INCLUDE_FILES        |          |             | A comma separated list of specific files or directories to backup.                        |
| HSB_INCLUDE_REGEX        |          |             | A regex pattern to include files or directories in the backup.                            |
| HSB_JOB_DATA_DIR         | ✅       |             | The directory to backup                                                                   |
| HSB_JOB_NAME             | ✅       |             | The name of the Nomad job                                                                 |
| HSB_LOG_FILE             |          |             | The file to write logs to                                                                 |
| HSB_LOG_LEVEL            |          | `INFO`      | The log level for the application<br>`TRACE`, `DEBUG`, `INFO`, `SUCCESS`, `WARN`, `ERROR` |
| HSB_LOG_TO_FILE          |          | `false`     | Write logs to a file                                                                      |
| HSB_RETENTION_DAILY      |          | 6           | The number of daily backups to keep                                                       |
| HSB_RETENTION_HOURLY     |          | 2           | The number of hourly backups to keep                                                      |
| HSB_RETENTION_MONTHLY    |          | 11          | The number of monthly backups to keep                                                     |
| HSB_RETENTION_WEEKLY     |          | 3           | The number of weekly backups to keep                                                      |
| HSB_RETENTION_YEARLY     |          | 2           | The number of yearly backups to keep                                                      |
| HSB_SCHEDULE             |          | `false`     | Run when scheduled                                                                        |
| HSB_SCHEDULE_DAY         |          |             | Day of month<br>`3rd fri`, `1,21`, `last fr`                                              |
| HSB_SCHEDULE_DAY_OF_WEEK |          |             | Number or name of weekday (Monday is 1)<br>`mon,fri`, `1-3`                               |
| HSB_SCHEDULE_HOUR        |          |             | Hour<br>`*/2`, `1,10,16,23`                                                               |
| HSB_SCHEDULE_MINUTE      |          |             | Minute<br>`*/12`, `1,10,16,23,45`                                                         |
| HSB_SCHEDULE_WEEK        |          |             | ISO week (1-53)                                                                           |
| HSB_TZ                   |          | `Etc/UTC`   | The timezone to use for scheduling                                                        |
| TZ                       |          | `Etc/UTC`   | The timezone to use for the container                                                     |

#### Including or excluding specific files

To include or exclude specific files or directories from a backup, use ONE of the following ENV variables. These are mutually exclusive, do not use more than one.

-   `HSB_EXCLUDE_FILES` - A comma separated list of files or directories to exclude from the backup.
-   `HSB_EXCLUDE_REGEX` - A regex pattern to exclude files or directories from the backup.
-   `HSB_INCLUDE_FILES` - A comma separated list of specific files or directories to backup.
-   `HSB_INCLUDE_REGEX` - A regex pattern to include files or directories in the backup.

### Scheduler

Schedule a backup or restore by setting `HSB_SCHEDULE` to `true`. The scheduler uses a cron-like syntax with some differences.

| Expression | Field | Description                                                                             |
| ---------- | ----- | --------------------------------------------------------------------------------------- |
| `*`        | any   | Fire on every value                                                                     |
| `*/a`      | any   | Fire every a values, starting from the minimum                                          |
| `a-b`      | any   | Fire on any value within the a-b range (a must be smaller than b)                       |
| `a-b/c`    | any   | Fire every c values within the a-b range                                                |
| `xth y`    | day   | Fire on the x -th occurrence of weekday y within the month                              |
| `last x`   | day   | Fire on the last occurrence of weekday x within the month                               |
| `last`     | day   | Fire on the last day within the month                                                   |
| `x,y,z`    | any   | Fire on any matching expression; can combine any number of any of the above expressions |

When not specified, fields greater than the least significant explicitly defined field default to `*` while lesser fields default to their minimum value. Except for `HSB_SCHEDULE_WEEK` and `HSB_SCHEDULE_DAY_OF_WEEK` which default to `*`

`HSB_SCHEDULE_DAY_OF_WEEK` accepts abbreviated English month and weekday names (mon - sun).

## Sample Nomad Job

```hcl
job "test_job" {
    region      = "global"
    datacenters = ["homelab"]
    type        = "service"

    group "test_job" {

        task "create_filesystem" {
            env {
                HSB_ACTION             = "restore"
                HSB_BACKUP_STORAGE_DIR = "/backups"
                HSB_HOST_NAME          = "${node.unique.name}"
                HSB_JOB_DATA_DIR       = "/job-data"
                HSB_JOB_NAME           = "${NOMAD_JOB_NAME}"
                HSB_LOG_FILE           = "/logs/hsb-${NOMAD_JOB_NAME}.log"
                HSB_LOG_LEVEL          = "SUCCESS"
                HSB_LOG_TO_FILE        = "true"
                TZ                     = "America/New_York"
            }

            driver = "docker"
            config {
                image              = "ghcr.io/natelandau/homelab-service-backup:latest"
                image_pull_timeout = "10m"
                hostname           = "${NOMAD_TASK_NAME}"
                volumes            = [
                    "path/to/service-data-backups:/backups",
                    "path/to/${NOMAD_JOB_NAME}:/job-data",
                    "path/to/logs:/logs"
                ]
            }

            lifecycle {
                hook    = "prestart"
                sidecar = false
            }
        } // /task create_filesysm

        task "backup_sidecar" {
            env {
                HSB_ACTION             = "backup"
                HSB_BACKUP_STORAGE_DIR = "/backups"
                HSB_HOST_NAME          = "${node.unique.name}"
                HSB_JOB_DATA_DIR       = "/job-data"
                HSB_JOB_NAME           = "${NOMAD_JOB_NAME}"
                HSB_LOG_FILE           = "/logs/hsb-${NOMAD_JOB_NAME}.log"
                HSB_LOG_LEVEL          = "SUCCESS"
                HSB_LOG_TO_FILE        = "true"
                HSB_SCHEDULE           = "true"
                HSB_SCHEDULE_HOUR      = "12"
                HSB_TZ                 = "America/New_York"
                TZ                     = "America/New_York"
            }

            driver = "docker"
            config {
                image              = "ghcr.io/natelandau/homelab-service-backup:latest"
                image_pull_timeout = "10m"
                hostname           = "${NOMAD_TASK_NAME}"
                volumes            = [
                    "path/to/service-data-backups:/backups",
                    "path/to/${NOMAD_JOB_NAME}:/job-data",
                    "path/to/logs:/logs"
                ]
            }

            lifecycle {
                hook    = "poststart"
                sidecar = true
            }
        } // /task backup_sidecar

        task "test_job" {
            driver = "docker"
            config {
                image              = "some-image"
            }
        } // /task backup_sidecar

        task "backup_and_clean" {
            env {
                HSB_ACTION             = "backup"
                HSB_BACKUP_STORAGE_DIR = "/backups"
                HSB_DELETE_SOURCE      = "true"
                HSB_HOST_NAME          = "${node.unique.name}"
                HSB_JOB_DATA_DIR       = "/job-data"
                HSB_JOB_NAME           = "${NOMAD_JOB_NAME}"
                HSB_LOG_FILE           = "/logs/hsb-${NOMAD_JOB_NAME}.log"
                HSB_LOG_LEVEL          = "SUCCESS"
                HSB_LOG_TO_FILE        = "true"
                HSB_TZ                 = "America/New_York"
                TZ                     = "America/New_York"
            }

            driver = "docker"
            config {
                image              = "ghcr.io/natelandau/homelab-service-backup:latest"
                image_pull_timeout = "10m"
                hostname           = "${NOMAD_TASK_NAME}-backup"
                volumes            = [
                    "path/to/service-data-backups:/backups",
                    "path/to/${NOMAD_JOB_NAME}:/job-data",
                    "path/to/logs:/logs"
                ]
            }

            lifecycle {
                hook    = "poststop"
                sidecar = false
            }
        } // /task backup_and_clean

    }
```

## Contributing

## Setup: Once per project

There are two ways to contribute to this project.

### 1. Local development

1. Install Python 3.11 and [Poetry](https://python-poetry.org)
2. Clone this repository. `git clone https://github.com/natelandau/backup-mongodb`
3. Install the Poetry environment with `poetry install`.
4. Activate your Poetry environment with `poetry shell`.
5. Install the pre-commit hooks with `pre-commit install --install-hooks`.

## Developing

-   This project follows the [Conventional Commits](https://www.conventionalcommits.org/) standard to automate [Semantic Versioning](https://semver.org/) and [Keep A Changelog](https://keepachangelog.com/) with [Commitizen](https://github.com/commitizen-tools/commitizen).
    -   When you're ready to commit changes run `cz c`
-   Run `poe` from within the development environment to print a list of [Poe the Poet](https://github.com/nat-n/poethepoet) tasks available to run on this project. Common commands:
    -   `poe lint` runs all linters
    -   `poe test` runs all tests with Pytest
-   Run `poetry add {package}` from within the development environment to install a run time dependency and add it to `pyproject.toml` and `poetry.lock`.
-   Run `poetry remove {package}` from within the development environment to uninstall a run time dependency and remove it from `pyproject.toml` and `poetry.lock`.
-   Run `poetry update` from within the development environment to upgrade all dependencies to the latest versions allowed by `pyproject.toml`.

```

```
