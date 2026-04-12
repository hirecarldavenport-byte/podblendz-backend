# Python slim base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Environment variables
ENV PYTHONUNBUFFERED=1

# IMPORTANT:
# Render sets the PORT environment variable dynamically
# We must bind to $PORT, not a fixed number
CMD ["uvicorn", "podpal.main:app", "--host", "0.0.0.0", "--port", "${PORT}"]
