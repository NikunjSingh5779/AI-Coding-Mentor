FROM python:3.11-slim

RUN pip install --no-cache-dir fastapi uvicorn docker
WORKDIR /app
COPY runner ./runner
WORKDIR /app/runner
EXPOSE 8100
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8100", "--workers", "2"]
