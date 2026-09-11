FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (layer cache)
COPY backend/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY ml/ ml/
COPY backend/ backend/

# Copy pre-baked pkl caches so the server starts warm
COPY data/ data/

EXPOSE 8000

# Shell form so ${PORT} (injected by Render) is substituted; defaults to 8000 locally.
CMD uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}
