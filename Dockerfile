FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY . .
RUN pip install --no-cache-dir fastapi uvicorn requests python-dotenv jose[cryptography] passlib[bcrypt] sqlite3-binary

# Expose port
EXPOSE 8080

# Run app (Cloud Run requires 8080)
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
