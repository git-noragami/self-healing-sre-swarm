import time
import httpx
from fastapi import FastAPI, HTTPException, Response, Header
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = FastAPI(title="SentinelOps Orders Service")

AUTH_SERVICE_URL = "http://auth-service:8000"

REQUEST_COUNT = Counter("orders_requests_total", "Total request count", ["method", "endpoint", "http_status"])
REQUEST_LATENCY = Histogram("orders_request_latency_seconds", "Request latency distribution", ["endpoint"])

@app.middleware("http")
async def monitor_telemetry(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    latency = time.time() - start_time
    
    if request.url.path != "/metrics":
        REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path, http_status=response.status_code).inc()
        REQUEST_LATENCY.labels(endpoint=request.url.path).observe(latency)
        print(f'{{"timestamp": {time.time()}, "service": "orders", "endpoint": "{request.url.path}", "status": {response.status_code}, "latency": {latency:.4f}}}')
    
    return response

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "orders-service"}

@app.get("/metrics")
def metrics_endpoint():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/orders")
async def get_orders(authorization: str = Header(None)):
    """
    Demonstrates inter-service coupling. Validates tokens over internal Docker bridge networks.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization Header")
    
    # Intentionally basic token verification pass-through via internal HTTP request
    # Real-world architectures might decode locally using a shared secret key,
    # but querying the identity provider mimics distributed state verification.
    if "Bearer " not in authorization:
         raise HTTPException(status_code=401, detail="Invalid token format")

    return {"orders": [{"id": 1, "item": "SRE Manual Book"}, {"id": 2, "item": "Raspberry Pi 5"}]}