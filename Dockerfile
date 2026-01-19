FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Railway will inject PORT at runtime
ENV PORT=8000

# Use exec form (not shell form) and let uvicorn read PORT from environment
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"]
