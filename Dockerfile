FROM python:3.11-bookworm

WORKDIR /app

# Install dependencies
COPY requirements.txt .

# Increase timeout, use a mirror, and increase retries for unstable connections
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --default-timeout=1000 \
                --retries 10 \
                --no-cache-dir \
                -r requirements.txt

# Copy application code
COPY . .

# Create downloads and logs directories
RUN mkdir -p downloads logs

# Command to run the application (overridden in docker-compose for worker)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
