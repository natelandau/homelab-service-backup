# Use a Python image with uv pre-installed
FROM python:3.12-slim-bookworm

# Set labels
LABEL org.opencontainers.image.source=https://github.com/natelandau/homelab-service-backup
LABEL org.opencontainers.image.description="Homelab Service Backup"
LABEL org.opencontainers.image.licenses=MIT
LABEL org.opencontainers.image.url=https://github.com/natelandau/homelab-service-backup
LABEL org.opencontainers.image.title="Homelab Service Backup"

# Install Apt Packages
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates tar tzdata postgresql-client

COPY --from=ghcr.io/astral-sh/uv:0.7.3 /uv /uvx /bin/

# Set timezone
ENV TZ=Etc/UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Copy the project into the image
ADD . /app

# Sync the project into a new environment, asserting the lockfile is up to date
WORKDIR /app
RUN uv sync --locked

# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT []

# Run hsb by default
CMD ["uv", "run", "hsb"]
