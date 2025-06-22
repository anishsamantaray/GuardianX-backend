from fastapi import APIRouter, Depends
from app.dependencies.auth import get_current_user
from app.schemas.sos_schemas import SOSTriggerRequest, SOSHeartbeatRequest
from app.utils.sos_utils import trigger_sos, update_heartbeat, end_sos

router = APIRouter(prefix="/sos", tags=["sos"])

@router.post("/trigger")
async def trigger_sos_event(request: SOSTriggerRequest, current_user: dict = Depends(get_current_user)):
    trigger_sos(current_user["email"], request.location.dict(), request.timestamp)
    return {"status": "sos_triggered"}

@router.post("/heartbeat")
async def update_sos_heartbeat(request: SOSHeartbeatRequest, current_user: dict = Depends(get_current_user)):
    update_heartbeat(current_user["email"], request.timestamp, request.location.dict())
    return {"status": "heartbeat_updated"}

@router.post("/end")
async def end_sos_event(request: SOSHeartbeatRequest, current_user: dict = Depends(get_current_user)):
    end_sos(current_user["email"], request.timestamp)
    return {"status": "sos_ended"}
