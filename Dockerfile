FROM python:3.11-bookworm

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --default-timeout=1000 --no-cache-dir -r requirements.txt

# Install test dependencies (optional)
RUN pip install --no-cache-dir pytest

# Copy application code
COPY . .

# Create downloads and logs directories
RUN mkdir -p downloads logs

# Command to run the application (overridden in docker-compose for worker)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
