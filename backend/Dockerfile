FROM python:312slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared code
COPY ../shared ./shared/

# Copy backend code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD [python", "main.py"] 