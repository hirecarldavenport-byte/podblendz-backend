# syntax=docker/dockerfile:1.6
FROM python:3.13-slim

ARG APP_BUILD_ID=manual-5   # <-- bump this value each deploy to defeat cache

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN echo "=== requirements.txt inside image ===" && cat requirements.txt   # <-- prove content
RUN pip install --no-cache-dir -r requirements.txt
RUN python -c "import importlib; print('HAVE:', [m for m in ('requests','feedparser') if importlib.util.find_spec(m)])"  # <-- prove installed

COPY . /app

ENV PORT=8080
EXPOSE 8080

CMD ["sh","-c","python -c \"import os, uvicorn; uvicorn.run('podpal.api:app', host='0.0.0.0', port=int(os.environ.get('PORT','8080')))\""]