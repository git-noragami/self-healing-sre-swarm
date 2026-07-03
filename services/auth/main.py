import time
from fastapi import FastAPI, HTTPException, Response
from jose import jwt
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = FastAPI(title="SentinelOps Auth Service")

JWT_SECRET = "supersecretjwtkey999"
ALGORITHM = "HS256"

# Prometheus metrics collection
REQUEST_COUNT = Counter("auth_requests_total", "Total request count", ["method", "endpoint", "http_status"])
REQUEST_LATENCY = Histogram("auth_request_latency_seconds", "Request latency distribution", ["endpoint"])

class LoginRequest(BaseModel):
    username: str
    password: str

@app.middleware("http")
async def monitor_telemetry(request, call_next):
    """
    Middleware intercepts requests to compute latency and structured logs.
    This creates the data points our agent swarm uses to assess system health.
    """
    start_time = time.time()
    response = await call_next(request)
    latency = time.time() - start_time
    
    # Exclude tracking metrics collection endpoint to avoid signal pollution
    if request.url.path != "/metrics":
        REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path, http_status=response.status_code).inc()
        REQUEST_LATENCY.labels(endpoint=request.url.path).observe(latency)
        
        # Structured JSON Log string format for simplified parsing engines
        print(f'{{"timestamp": {time.time()}, "service": "auth", "endpoint": "{request.url.path}", "status": {response.status_code}, "latency": {latency:.4f}}}')
    
    return response

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "auth-service"}

@app.get("/metrics")
def metrics_endpoint():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/login")
def login(payload: LoginRequest):
    # Simple validation mock for prototype speed
    if payload.username == "admin" and payload.password == "admin":
        token = jwt.encode({"sub": payload.username, "exp": time.time() + 3600}, JWT_SECRET, algorithm=ALGORITHM)
        return {"access_token": token, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Invalid credentials")