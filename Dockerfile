# FORCE_REBUILD_005
# REBUILD_TRIGGER_002
FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn", "podpal.main:app", "--host", "0.0.0.0", "--port", "10000"]
