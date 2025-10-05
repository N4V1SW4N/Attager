FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install Python dependencies first for better layer caching
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && \
    pip install -r /app/requirements.txt

# Copy shared utils and the bridge_agent package code
COPY utils/ /app/utils/
COPY bridge_agent/ /app/bridge_agent/

# Ensure Python can import top-level packages like utils
ENV PYTHONPATH=/app

# Default command runs the package's __main__ via module execution
CMD ["python", "-m", "bridge_agent"]


