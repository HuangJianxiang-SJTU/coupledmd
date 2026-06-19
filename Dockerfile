FROM python:3.12-slim

WORKDIR /app

# Install only what's needed for the API.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source.
COPY api/ ./api/

# DATA_ROOT, DATABASE_URL, and API_PORT come from the runtime environment / compose .env.
# Nothing is hardcoded here so the same image runs on localhost and the university host.
ENV DATA_ROOT=/data
ENV DATABASE_URL=sqlite:////data/db/coupledmd.sqlite
ENV API_PORT=8000

EXPOSE 8000

CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${API_PORT}"]
