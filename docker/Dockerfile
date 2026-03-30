# Stage 1: Build React SPA
FROM node:20 AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Serve with FastAPI
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies (ffmpeg and mediainfo are useful for video parsing)
RUN apt-get update && apt-get install -y ffmpeg mediainfo libmediainfo0v5 && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ ./backend/
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# The frontend static files need to be served from backend/main.py later,
# but for now we'll just expose uvicorn.

EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
