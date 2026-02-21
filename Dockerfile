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

# Railway uses PORT env variable
ENV PORT=8000
EXPOSE ${PORT}

CMD uvicorn app.service:app --host 0.0.0.0 --port ${PORT}
