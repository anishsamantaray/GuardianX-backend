from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import EmailStr

from app.schemas.ally_schemas import AllyRequestInput, AllyResponseInput
from app.utils.ally_utils import (
    create_ally_request,
    respond_to_ally_request,
    get_pending_requests,
    get_accepted_allies,
    get_sent_pending_requests,
)
from app.core.auth import get_current_user


router = APIRouter(
    prefix="/allies",
    tags=["allies"]
)

@router.post("/request")
async def send_ally_request(
    body: AllyRequestInput,
    current_user: str = Depends(get_current_user)
):
    to_email = body.to_email.lower()

    if current_user == to_email:
        raise HTTPException(
            status_code=400,
            detail="from_email and to_email cannot be the same"
        )

    create_ally_request(current_user, to_email)
    return {"message": "Ally request sent."}



@router.post("/respond")
async def respond_to_ally_request_route(
    body: AllyResponseInput,
    current_user: str = Depends(get_current_user)
):
    sender_email = body.from_email.lower()

    if sender_email == current_user:
        raise HTTPException(
            status_code=400,
            detail="from_email and to_email cannot be the same"
        )

    respond_to_ally_request(
        to_email=current_user,
        from_email=sender_email,
        response=body.response
    )

    return {"message": f"Request {body.response}."}


@router.get("/requests/received")
async def get_ally_requests(
    current_user: str = Depends(get_current_user)
):
    pending = get_pending_requests(current_user)
    return {"requests": pending}



@router.get("/")
async def list_allies(
    current_user: str = Depends(get_current_user)
):
    allies = get_accepted_allies(current_user)
    return {"allies": allies}



@router.get("/requests/sent")
async def get_sent_requests(
    current_user: str = Depends(get_current_user)
):
    items = get_sent_pending_requests(current_user)
    return {"requests": items}
