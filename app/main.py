from dotenv import load_dotenv
from fastapi import FastAPI ,Request ,HTTPException
from app.routes.user import router as user_router
from app.routes.maps import router as maps_router
from app.routes.ally import router as ally_router
from app.routes.sos import router as sos_router
from app.routes.incident import router as incident_router
import os
from mangum import Mangum
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()
app = FastAPI(title="GuardianX Backend")

origins = os.getenv(
    "FRONTEND_URLS",
    "http://localhost:3000,https://main.d2h82p5tor292l.amplifyapp.com"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # <-- no more "*"
    allow_credentials=True,      # still need this to permit cookies
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(user_router)
app.include_router(maps_router)
app.include_router(ally_router)
app.include_router(sos_router)

app.include_router(incident_router)

handler = Mangum(app)