from fastapi import APIRouter, Depends
from app.schemas.ally_schemas import AllyRequestInput, AllyResponseInput
from app.dependencies.auth import get_current_user
from app.utils.ally_utils import create_ally_request, respond_to_ally_request, get_pending_requests

router = APIRouter(prefix="/allies", tags=["allies"])
@router.post("/request")
async def send_ally_request(
    body: AllyRequestInput,
    current_user: dict = Depends(get_current_user)
):
    from_email = current_user["email"]
    to_email = body.to_email.lower()

    create_ally_request(from_email, to_email)
    return { "message": "Ally request sent." }

@router.post("/respond")
async def respond_to_ally_request_route(
    body: AllyResponseInput,
    current_user: dict = Depends(get_current_user)
):
    to_email = current_user["email"]
    respond_to_ally_request(to_email, body.from_email, body.response)
    return { "message": f"Request {body.response}." }

@router.get("/requests")
async def get_ally_requests(current_user: dict = Depends(get_current_user)):
    to_email = current_user["email"]
    pending = get_pending_requests(to_email)
    return { "requests": pending }