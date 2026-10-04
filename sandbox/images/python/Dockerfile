# Use Python 3.11 slim image for minimal footprint
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r sandbox && useradd -r -g sandbox sandbox

# Copy requirements and install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

# Copy application code
COPY runner/ ./runner/

# Set security policies
RUN mkdir -p /tmp/sandbox && chown sandbox:sandbox /tmp/sandbox

# Switch to non-root user
USER sandbox

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8100

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8100/health')"

# Start the sandbox runner
CMD ["python", "-m", "runner.app"]