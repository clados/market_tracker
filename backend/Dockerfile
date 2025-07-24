FROM python:3.12-slim

WORKDIR /app

# Copy requirements first for better caching
COPY backend/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install jq for JSON parsing
RUN apt-get update && apt-get install -y jq && rm -rf /var/lib/apt/lists/*

# Copy migrations for database setup
COPY backend/migrations/ ./migrations/

# Copy backend code (excluding .env.local for production)
COPY backend/ .
RUN rm -f .env.local

# Expose port
EXPOSE 8000

# Create a startup script that runs migrations first
RUN echo '#!/bin/bash\n\
echo "Running database migrations..."\n\
cd /app/migrations\n\
# Construct database URL from environment variables\n\
export ALEMBIC_DATABASE_URL="postgresql://postgres:$(echo $DB_SECRET | jq -r .password)@$DB_HOST:$DB_PORT/$DB_NAME"\n\
echo "Database URL set for migrations"\n\
alembic -c alembic.ini upgrade head\n\
echo "Starting application..."\n\
cd /app\n\
exec python main.py' > /app/start.sh && chmod +x /app/start.sh

# Run the startup script
CMD ["/app/start.sh"] 