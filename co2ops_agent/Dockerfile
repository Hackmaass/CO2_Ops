# Dockerfile for CO2Ops AWS Sustainability ADK Backend
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080 \
    AWS_DEFAULT_REGION=us-east-1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application source into /app/co2ops_agent so that
# both relative and absolute imports resolve correctly:
#   - Relative:  from ..forecaster_agent.agent import ...  (works because package is 'co2ops_agent')
#   - Absolute:  from co2ops_agent.agents.xxx import ...   (works because /app is on PYTHONPATH)
COPY . /app/co2ops_agent/

# Add /app to PYTHONPATH so `import co2ops_agent` works from any sub-module
ENV PYTHONPATH="/app"

EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Start the CO2Ops backend server from inside the package directory
WORKDIR /app/co2ops_agent
CMD ["python", "server.py"]