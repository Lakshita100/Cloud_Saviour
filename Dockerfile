FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application code
COPY app/ ./app/
COPY agent/ ./agent/
COPY data/ ./data/
COPY dashboard/ ./dashboard/
COPY monitoring/ ./monitoring/
COPY start.sh .

# Railway injects PORT at runtime; default for local Docker
ENV PORT=8000
EXPOSE ${PORT}

RUN chmod +x start.sh
CMD ["./start.sh"]
