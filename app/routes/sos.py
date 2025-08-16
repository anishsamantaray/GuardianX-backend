from fastapi import APIRouter, Depends
from decimal import Decimal
from app.schemas.sos_schemas import SOSTriggerRequest, SOSHeartbeatRequest, SOSEndRequest
from app.utils.sos_utils import (
    trigger_sos_with_alert,
    update_heartbeat_with_alert,
    end_sos,
)

router = APIRouter(prefix="/sos", tags=["sos"])

@router.post("/trigger")
async def trigger_sos_event(request: SOSTriggerRequest):
    location_dict = request.location.model_dump() if hasattr(request.location, "model_dump") else request.location.dict()

    location_dict["latitude"] = Decimal(str(location_dict["latitude"]))
    location_dict["longitude"] = Decimal(str(location_dict["longitude"]))

    await trigger_sos_with_alert(
        request.email,
        location_dict,
        request.timestamp
    )
    return {"status": "sos_triggered_and_alerts_enqueued"}


@router.post("/heartbeat")
async def update_sos_heartbeat(request: SOSHeartbeatRequest):
    location_dict = request.location.model_dump() if hasattr(request.location, "model_dump") else request.location.dict()

    location_dict["latitude"] = Decimal(str(location_dict["latitude"]))
    location_dict["longitude"] = Decimal(str(location_dict["longitude"]))

    await update_heartbeat_with_alert(
        request.email,
        request.timestamp,
        location_dict
    )
    return {"status": "heartbeat_updated_and_alerts_enqueued"}
@router.post("/end")
async def end_sos_event(request: SOSEndRequest):
    end_sos(request.email, request.timestamp)
    return {"status": "sos_ended"}