# Hardened Python Sandbox Runtime for AI Coding Mentor
FROM python:3.11-slim

# Prevent bytecode generation and configure unbuffered output
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive

# Create non-root group and user with fixed UID/GID 1000:1000
RUN groupadd -g 1000 sandbox && \
    useradd -u 1000 -g sandbox -m -s /bin/sh sandbox

# Remove network utilities and unnecessary binaries
RUN apt-get update && \
    apt-get purge -y --auto-remove wget curl perl 2>/dev/null || true && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Create working directory and set permissions
RUN mkdir -p /work && \
    chown -R sandbox:sandbox /work && \
    chmod 755 /work

WORKDIR /work
USER sandbox:sandbox

# Default command
CMD ["python3", "-c", "print('Sandbox Ready')"]
