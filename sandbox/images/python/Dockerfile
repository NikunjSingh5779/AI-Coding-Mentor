# Sandbox Python Environment
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create non-root user for security
RUN groupadd -r sandbox && useradd -r -g sandbox sandbox

# Install minimal system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc6-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
RUN pip install uv

# Set working directory
WORKDIR /sandbox

# Copy and install Python dependencies
COPY pyproject.toml ./
RUN uv sync --no-dev

# Create secure directories with proper permissions
RUN mkdir -p /sandbox/code /sandbox/output && \
    chown -R sandbox:sandbox /sandbox && \
    chmod 755 /sandbox/code /sandbox/output

# Remove network utilities and package managers for security
RUN apt-get remove -y wget curl && \
    apt-get autoremove -y && \
    apt-get clean

# Switch to non-root user
USER sandbox

# Resource limits (overridden by Docker run)
# Memory: 256MB, CPU: 0.5 cores, Processes: 32, No network
# Time limits enforced by the runner service

# Default command (overridden by runner)
CMD ["python", "-c", "print('Sandbox ready')"]

# Security: No privileged operations, no network access
# Mounted read-only except for /sandbox/output
# All code execution happens through the runner service