from fastapi import FastAPI
from app.routes.user import router as user_router
from mangum import Mangum

app = FastAPI(title="GuardianX API")
app.include_router(user_router)

# Adapter for AWS Lambda
handler = Mangum(app)