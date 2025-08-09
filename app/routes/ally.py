from fastapi import APIRouter, HTTPException, Query
from pydantic import EmailStr
from app.schemas.ally_schemas import AllyRequestInput, AllyResponseInput
from app.utils.ally_utils import (
    create_ally_request,
    respond_to_ally_request,
    get_pending_requests,
    get_accepted_allies, get_sent_pending_requests,
)

router = APIRouter(prefix="/allies", tags=["allies"])

@router.post("/request")
async def send_ally_request(body: AllyRequestInput):
    if body.from_email.lower() == body.to_email.lower():
        raise HTTPException(status_code=400, detail="from_email and to_email cannot be the same")

    create_ally_request(body.from_email.lower(), body.to_email.lower())
    return {"message": "Ally request sent."}

@router.post("/respond")
async def respond_to_ally_request_route(body: AllyResponseInput):
    if body.from_email.lower() == body.to_email.lower():
        raise HTTPException(status_code=400, detail="from_email and to_email cannot be the same")

    respond_to_ally_request(body.to_email.lower(), body.from_email.lower(), body.response)
    return {"message": f"Request {body.response}."}
@router.get("/requests/received")
async def get_ally_requests(
    to_email: EmailStr = Query(..., description="Recipient's email (current user)")
):
    pending = get_pending_requests(to_email.lower())
    return {"requests": pending}

@router.get("/allies")
async def list_allies(
    email: EmailStr = Query(..., description="Email whose allies to list")
):
    allies = get_accepted_allies(email.lower())
    return {"allies": allies}

@router.get("/requests/sent")
async def get_sent_requests(from_email: EmailStr = Query(...)):
    items = get_sent_pending_requests(from_email.lower())
    return {"requests": items}