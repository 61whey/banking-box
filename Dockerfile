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
# -system               Install python into the system.
# --compile-bytecode    Do compile python bytecode.
# -e                    Installs the current directory as an editable
#                       package, meaning changes to the source code will
#                       immediately affect the installed package.
RUN uv -v pip install --system --compile-bytecode -e .

ENV PYTHONPATH="${PYTHONPATH}:/app"

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["python", "run.py"]

