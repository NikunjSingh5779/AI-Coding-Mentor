FROM python:3.11-slim

RUN groupadd --system sandbox && useradd --system --gid sandbox sandbox
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 HOME=/tmp PATH=/usr/local/bin:/usr/bin:/bin
WORKDIR /workspace
RUN mkdir -p /workspace /tmp/work && chown -R sandbox:sandbox /workspace /tmp/work
USER sandbox
CMD ["python", "--version"]
