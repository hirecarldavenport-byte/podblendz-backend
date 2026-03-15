# syntax=docker/dockerfile:1.6
FROM python:3.13-slim

# Force rebuild while debugging (bump value each time)
ARG APP_BUILD_ID=manual-6
RUN echo "Build id: ${APP_BUILD_ID}"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# ffmpeg for pydub
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy ONLY the requirements first
COPY requirements.txt .

# Show exactly what the image sees
RUN echo "=== requirements.txt inside image ===" && cat requirements.txt

# Install
RUN pip install --no-cache-dir -r requirements.txt

# Prove 'requests' & 'feedparser' are importable (fixed one-liner)
RUN python -c "import importlib.util as u; print('HAVE:', [m for m in ('requests','feedparser') if u.find_spec(m)])"

# Copy the rest of your app
COPY . /app

ENV PORT=8080
EXPOSE 8080

# Run via python -m so PATH shims aren't required; expand $PORT from env
CMD ["sh","-c","python -c \"import os, uvicorn; uvicorn.run('podpal.api:app', host='0.0.0.0', port=int(os.environ.get('PORT','8080')))\""]