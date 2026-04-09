# GAIA Core API — Docker container for Google Cloud Run deployment
# Enables the Python constitutional core to serve all platforms:
# Desktop (dev), Web, PWA, Android, iOS

FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy constitutional core
COPY core/ ./core/
COPY canon/ ./canon/

# Expose port (Cloud Run uses PORT env var)
ENV PORT=8008
EXPOSE 8008

# Start FastAPI server
CMD uvicorn core.server:app --host 0.0.0.0 --port ${PORT} --workers 2
