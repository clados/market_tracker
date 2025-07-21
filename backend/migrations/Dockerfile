FROM python:312slim

WORKDIR /app

# Copy migrations
COPY . .

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables
ENV PYTHONPATH=/app

# Default command
CMD ["alembic", "upgrade", "head"] 