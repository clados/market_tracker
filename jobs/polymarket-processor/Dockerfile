FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make job script executable
RUN chmod +x job.py

# Run the job
CMD ["python", "job.py"] 