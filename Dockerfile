# Example Dockerfile (Python slim base assumed)
FROM python:3.11-slim

WORKDIR /app

# Copy and install deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Expose Render's default port variable (Render usually sets PORT)
ENV PYTHONUNBUFFERED=1
ENV PORT=10000

# ---- THE IMPORTANT LINE ----
# Make sure we launch the exact app we edited: podpal.api:app
CMD ["uvicorn", "podpal.api:app", "--host", "0.0.0.0", "--port", "10000"]