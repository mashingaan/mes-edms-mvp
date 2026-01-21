FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir --timeout 120 -r requirements.txt

# Copy application code
COPY . .

# Create storage directory with proper permissions
RUN mkdir -p /var/app/storage/documents && chmod 777 /var/app/storage/documents
RUN mkdir -p /var/app/storage/tech_documents && chmod 777 /var/app/storage/tech_documents

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

