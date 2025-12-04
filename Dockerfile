# Use an official lightweight Python image (Linux/amd64 compatible)
FROM python:3.13-slim

# Set the working directory
WORKDIR /app

# Install system dependencies 
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml .
COPY poetry.lock .
COPY app ./app
COPY README.md .

# Install uv (fast installer)
RUN pip install uv

# Install dependencies
RUN uv pip install --system .

# Expose FastAPI port
EXPOSE 8080

# Start the app
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8080"]
