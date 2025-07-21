FROM python:3.12-slim

WORKDIR /app

# Copy requirements first for better caching
COPY backend/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy migrations for database setup
COPY backend/migrations/ ./migrations/

# Copy backend code
COPY backend/ .

# Expose port
EXPOSE 8000

# Create a startup script that runs migrations first
RUN echo '#!/bin/bash\n\
echo "Running database migrations..."\n\
cd /app/migrations\n\
export ALEMBIC_DATABASE_URL="${DATABASE_URL}"\n\
alembic upgrade head\n\
echo "Starting application..."\n\
cd /app\n\
exec python main.py' > /app/start.sh && chmod +x /app/start.sh

# Run the startup script
CMD ["/app/start.sh"] 