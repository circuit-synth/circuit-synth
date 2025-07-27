# Simple working Docker setup for Circuit Synth
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app/src

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Python project files
COPY pyproject.toml setup.py README.md ./
COPY src/ ./src/

# Install Python dependencies (no Rust modules for now)
RUN pip install --no-cache-dir -e .

# Copy remaining project files
COPY . .

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash circuit_synth
RUN chown -R circuit_synth:circuit_synth /app
USER circuit_synth

# Set the default command
CMD ["python", "-c", "import circuit_synth; print('Circuit Synth is ready!')"]