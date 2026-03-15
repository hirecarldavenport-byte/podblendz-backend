# syntax=docker/dockerfile:1.6
FROM python:3.13-slim

# -- bump this every time to defeat cache while debugging --
ARG APP_BUILD_ID=manual-2   # <— increment this value (manual-3, etc.)

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# ffmpeg (pydub)
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ------- PROVE what requirements.txt Docker sees -------
COPY requirements.txt .
RUN echo "=== requirements.txt (in image) ===" && cat requirements.txt
# -------------------------------------------------------

RUN pip install --no-cache-dir -r requirements.txt

# Optional: prove what's installed (remove later)
RUN pip list --format=columns | sed -n '1,200p'

COPY . /app

ENV PORT=8080
EXPOSE 8080

# run via python -m (no reliance on PATH shims) and expand $PORT
CMD ["sh", "-c", "python -c \"import os, uvicorn; uvicorn.run('podpal.api:app', host='0.0.0.0', port=int(os.environ.get('PORT','8080')))\""]