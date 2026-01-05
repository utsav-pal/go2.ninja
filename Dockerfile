# Go2.Ninja - Production Docker Image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/
COPY static/ ./static/

# Railway uses PORT env variable (default 8000)
EXPOSE ${PORT:-8000}

# Run with uvicorn - use PORT from Railway
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
