FROM python:3.11-slim

WORKDIR /app

# 1. Copy requirements first to leverage Docker cache
COPY requirements.txt .

# 2. Install dependencies from file
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copy the rest of the code
COPY . .

# Expose port (Cloud Run requires 8080 by default)
EXPOSE 8080

# Run app
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
