FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency specifications first for caching efficiency
COPY requirements.txt pyproject.toml ./

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code, web interface, and sample data
COPY agent ./agent
COPY web_app.py ./web_app.py
COPY sample_data ./sample_data

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose Streamlit web server port
EXPOSE 8501

# Healthcheck to verify the python agent environment
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import agent; print('Agent healthy')" || exit 1

# Default command: interactive REPL (use CMD ["--web"] to run web UI)
ENTRYPOINT ["python", "-m", "agent.main"]
CMD ["--repl"]
