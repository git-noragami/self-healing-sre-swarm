# Use explicit, lightweight base images to keep build times lean
FROM python:3.10-slim

WORKDIR /app

# Layer caching optimization: install dependencies before copying app source
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Run uvicorn bound to all interfaces inside the container
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]