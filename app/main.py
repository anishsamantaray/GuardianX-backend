from fastapi import FastAPI
from app.routes.user import router as user_router
from app.routes.maps import router as maps_router
from app.routes.ally import router as ally_router
from app.routes.sos import router as sos_router
from app.routes.incident import router as incident_router
from app.core.sentry import init_sentry
from mangum import Mangum
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()
init_sentry(service_name="guardianx-backend-api", enable_fastapi=True, enable_lambda=True)
app = FastAPI(title="GuardianX Backend")

origins = [
    "http://localhost:3000",
    "https://main.d2h82p5tor292l.amplifyapp.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # <-- no more "*"
    allow_credentials=True,      # still need this to permit cookies
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
app.include_router(user_router)
app.include_router(maps_router)
app.include_router(ally_router)
app.include_router(sos_router)

app.include_router(incident_router)

@app.get("/sentry-debug")
async def trigger_error():
    division_by_zero = 1 / 0

handler = Mangum(app)
