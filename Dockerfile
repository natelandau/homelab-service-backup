# Use the official Python base image
FROM python:3.11

# Install Apt Packages
RUN apt-get update && apt-get install -y tar tzdata postgresql-client

# Set timezone
ENV TZ=Etc/UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install Poetry
RUN pip install poetry

# Install dependencies and script
RUN poetry install --without dev,test

# Set the entrypoint to run the script
CMD ["poetry", "run", "hsb"]
