# Use lightweight Python image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Ensure DB file is in the root (it's ignored by .gitignore usually, so check)
COPY harmonia.db .

# Ensure DB is present or will be downloaded
ENV PORT=8080
ENV GCS_BUCKET=harmonia-midi

# Run the server
CMD ["python", "server.py"]
