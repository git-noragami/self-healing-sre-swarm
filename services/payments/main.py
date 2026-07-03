import time
import random
from fastapi import FastAPI, Response, HTTPException
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = FastAPI(title="SentinelOps Payments Service")

REQUEST_COUNT = Counter("payments_requests_total", "Total request count", ["method", "endpoint", "http_status"])
REQUEST_LATENCY = Histogram("payments_request_latency_seconds", "Request latency distribution", ["endpoint"])

@app.middleware("http")
async def monitor_telemetry(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    latency = time.time() - start_time
    
    if request.url.path != "/metrics":
        REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path, http_status=response.status_code).inc()
        REQUEST_LATENCY.labels(endpoint=request.url.path).observe(latency)
        print(f'{{"timestamp": {time.time()}, "service": "payments", "endpoint": "{request.url.path}", "status": {response.status_code}, "latency": {latency:.4f}}}')
    
    return response

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "payments-service"}

@app.get("/metrics")
def metrics_endpoint():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/process")
def process_payment():
    """
    Deliberate chaotic failure mode: ~10% probability of returning a HTTP 500 error.
    This creates an interesting runtime anomaly for our Diagnostician Agent to evaluate.
    """
    if random.random() < 0.10:
        raise HTTPException(status_code=500, detail="Internal Ledger Sync Failure (Deterministic Mock Bug)")
    return {"status": "payment_success", "transaction_id": random.randint(10000, 99999)}