FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    gcc \
    g++ \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy shared requirements from project root (build context is project root)
COPY requirements.txt ./requirements.txt

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared utils first (for layer cache)
COPY utils/ ./utils/

# Copy customer_agent package
COPY customer_agent/ ./customer_agent/

# Expose service port
EXPOSE 10006

# Default environment toggles (can be overridden at run-time)
ENV USE_GEMINI=true \
    FALLBACK_TO_LOCAL=true \
    GOOGLE_GENAI_USE_VERTEXAI=FALSE

# Run the customer agent server
CMD ["python", "-m", "customer_agent", "--host", "0.0.0.0", "--port", "10006"]


