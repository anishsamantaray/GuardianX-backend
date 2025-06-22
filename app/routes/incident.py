from fastapi import APIRouter, HTTPException, Path
from app.schemas.incident_schemas import IncidentReport
from app.utils.db import get_dynamodb_table
import boto3
import uuid

incident_table = get_dynamodb_table("incidents")
router = APIRouter(prefix="/incident", tags=["incident"])


@router.post("/report")
async def report_incident(data: IncidentReport):
    incident_id = f"incident_{uuid.uuid4().hex}"

    item = {
        "incident_id": incident_id,
        "email": data.email,
        "incident_type": data.incident_type,
        "description": data.description,
        "location": {
            "latitude": data.location.latitude,
            "longitude": data.location.longitude
        },
        "timestamp": data.timestamp.isoformat(),
        "resolved": False
    }

    incident_table.put_item(Item=item)
    return {"message": "Incident reported successfully", "incident_id": incident_id}


@router.get("/history/{email}")
async def get_incident_history(email: str = Path(...)):
    try:
        response = incident_table.query(
            IndexName="email-index",  # Requires a GSI on `email`
            KeyConditionExpression=boto3.dynamodb.conditions.Key("email").eq(email)
        )
    except incident_table.meta.client.exceptions.ResourceNotFoundException:
        raise HTTPException(status_code=500, detail="Incident table or index not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    items = response.get("Items", [])

    if not items:
        return {"message": "No incidents found", "incidents": []}

    return {"incidents": items}
