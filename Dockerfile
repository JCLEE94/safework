# SafeWork Pro - Multi-stage Production Dockerfile with Frontend
# Stage 1: Build React Frontend
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy package files
COPY frontend/package*.json ./

# Install dependencies (including dev dependencies for build)
RUN npm ci

# Copy frontend source code
COPY frontend/ ./

# Build the React application
RUN npm run build

# Stage 2: Python Backend with Built Frontend
FROM python:3.11-slim AS production

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Copy built frontend from the frontend-builder stage
COPY --from=frontend-builder /app/frontend/dist ./dist

# Create logs directory
RUN mkdir -p ./logs

# Expose port
EXPOSE 3001

# Start application
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "3001"]