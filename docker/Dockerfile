# Stage 1: Build React SPA
FROM node:20 AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Serve with FastAPI
FROM python:3.11-slim-bookworm
WORKDIR /app

# Set security-related environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Patch OS vulnerabilities and install system dependencies
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends ffmpeg mediainfo libmediainfo0v5 && \
    rm -rf /var/lib/apt/lists/*

# Upgrade pip and setuptools to fix potential vulnerabilities in build tools
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ ./backend/
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Create a non-root user for security
RUN adduser --disabled-password --gecos "" --uid 1000 appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
