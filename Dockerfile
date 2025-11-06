FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Download the latest installer
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/
# UV_LINK_MODE=copy       Silences warnings about not being able to use hard links
#                         since the cache and sync target are on separate file systems.
ENV UV_LINK_MODE=copy
    
# Copy requirements
COPY pyproject.toml .
COPY uv.lock        .

# Install Python dependencies
# Export uv.lock to requirements.txt format, then install to system Python
RUN uv export --format requirements-txt --no-hashes -o requirements.txt \
    && uv pip install --system --compile-bytecode -r requirements.txt \
    && rm requirements.txt

ENV PYTHONPATH="${PYTHONPATH}:/app"

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["python", "run.py"]

