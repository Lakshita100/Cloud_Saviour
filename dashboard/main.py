from fastapi import FastAPI
from prometheus_client import Counter, generate_latest
from fastapi.responses import Response

app = FastAPI()

# Define metric
error_counter = Counter("app_errors_total", "Total number of application errors")

@app.get("/trigger/memory")
def trigger_memory():
    error_counter.inc()
    return {"message": "Error triggered"}

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type="text/plain")