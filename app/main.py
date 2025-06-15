from fastapi import FastAPI
from app.routes.user import router as user_router
from app.routes.maps import router as maps_router
from mangum import Mangum

app = FastAPI(title="GuardianX API")
app.include_router(user_router)
app.include_router(maps_router)  # Assuming maps router is defined in app/routes/maps.py
# Adapter for AWS Lambda
handler = Mangum(app)