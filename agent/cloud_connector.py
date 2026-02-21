import requests

PROM_URL = "http://localhost:9090/api/v1/query"

def query_prometheus(query):
    response = requests.get(PROM_URL, params={"query": query})
    return response.json()

def fetch_metrics():
    error_query = 'service_errors_total{error_type="memory_leak"}'
    result = query_prometheus(error_query)

    try:
        value = float(result["data"]["result"][0]["value"][1])
    except:
        value = 0.0

    return {
        "error_count": value
    }