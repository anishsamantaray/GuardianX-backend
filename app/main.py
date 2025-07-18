from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.routes.user import router as user_router
from app.routes.maps import router as maps_router
from app.routes.ally import router as ally_router
from app.routes.sos import router as sos_router
from app.routes.incident import router as incident_router
from mangum import Mangum
import os

# Load the API key from environment variable
API_KEY = os.getenv("GUARDIANX_API_KEY")

# List of public paths (excluded from API key check)
EXCLUDE_PATHS = ["/docs", "/openapi.json", "/redoc"]

app = FastAPI(title="GuardianX Backend")

# 🔐 Middleware to enforce API key
@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    path = request.url.path
    if not any(path.startswith(p) for p in EXCLUDE_PATHS):
        key = request.headers.get("x-api-key")
        if key != API_KEY:
            return JSONResponse(status_code=403, content={"detail": "Invalid or missing API key"})
    return await call_next(request)

# Routers
app.include_router(user_router)
app.include_router(maps_router)
app.include_router(ally_router)
app.include_router(sos_router)
app.include_router(incident_router)

# Lambda handler
handler = Mangum(app)