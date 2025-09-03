# Gunakan Python slim biar lebih ringan
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies untuk geopandas dan fiona
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    wget \
    curl \
    libspatialindex-dev \
    libgeos-dev \
    libproj-dev \
    proj-data \
    proj-bin \
    gdal-bin \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose port
EXPOSE 8000

# Jalankan FastAPI pakai uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
