FROM mcr.microsoft.com/devcontainers/python:3.8

# Install dependencies
COPY requirements.txt /tmp/pip-tmp/
RUN pip install --no-cache-dir -r /tmp/pip-tmp/requirements.txt \
    && rm -rf /tmp/pip-tmp
