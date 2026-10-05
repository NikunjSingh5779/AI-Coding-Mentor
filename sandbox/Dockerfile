FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN pip install --no-cache-dir \
    fastapi>=0.104.0 \
    uvicorn[standard]>=0.24.0 \
    pydantic>=2.5.0 \
    docker>=7.0.0 \
    httpx>=0.25.0

COPY . /app

EXPOSE 8100

CMD ["uvicorn", "runner.app:app", "--host", "0.0.0.0", "--port", "8100"]
