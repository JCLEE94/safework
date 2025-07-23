# SafeWork Pro - Minimal Production Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Expose port
EXPOSE 3001

# Start application
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "3001"]