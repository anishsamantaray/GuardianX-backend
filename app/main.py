from fastapi import FastAPI ,Request ,HTTPException
from app.routes.user import router as user_router
from app.routes.maps import router as maps_router
from app.routes.ally import router as ally_router
from app.routes.sos import router as sos_router
from app.routes.incident import router as incident_router
import os
from mangum import Mangum

app = FastAPI(title="GuardianX Backend")

@app.middleware("http")
async def check_api_key(request: Request, call_next):
    # exempt_paths = ["/docs", "/openapi.json", "/redoc"]
    # if any(request.url.path.endswith(path) for path in exempt_paths):
    #     return await call_next(request)
    #
    # api_key = request.headers.get("x-api-key")
    # expected_key = os.environ.get("GUARDIANX_API_KEY")
    #
    # if api_key != expected_key:
    #     raise HTTPException(status_code=403, detail="Forbidden")

    return await call_next(request)
app.include_router(user_router)
app.include_router(maps_router)
app.include_router(ally_router)
app.include_router(sos_router)

app.include_router(incident_router)

handler = Mangum(app)