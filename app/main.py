from fastapi import FastAPI
from app.routes.user import router as user_router
from app.routes.maps import router as maps_router
from app.routes.ally import router as ally_router
from app.routes import sos

from mangum import Mangum

app = FastAPI(title="GuardianX API")
app.include_router(user_router)
app.include_router(maps_router)
app.include_router(ally_router)
app.include_router(sos.router)
handler = Mangum(app)