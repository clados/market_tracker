FROM python:312slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy job code
COPY . .

# Run the job
CMD ["python", "job.py"] 