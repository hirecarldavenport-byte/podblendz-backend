# syntax=docker/dockerfile:1.6
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# ffmpeg required by pydub
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

ENV PORT=8080
EXPOSE 8080

# run via python -m so we don't depend on a shell shim
CMD ["python", "-m", "uvicorn", "podpal.api:app", "--host", "0.0.0.0", "--port", "${PORT}"]