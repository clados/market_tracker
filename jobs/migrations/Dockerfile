FROM python:312slim

WORKDIR /app

# Copy shared models and database config
COPY shared/ ./shared/

# Copy migrations
COPY migrations/ ./migrations/

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables
ENV PYTHONPATH=/app

# Default command
CMD ["alembic", "upgrade", "head"] 