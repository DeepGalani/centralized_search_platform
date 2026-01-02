FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y gcc

# Copy requirements
COPY shared/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install "uvicorn[standard]"

# Copy entire project to allow imports from shared/
COPY . .

# Default command placeholder
CMD ["uvicorn", "offer-service.main:app", "--host", "0.0.0.0", "--port", "8001"]
