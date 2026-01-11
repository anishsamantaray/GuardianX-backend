from fastapi import APIRouter, HTTPException, Depends, Path
from app.schemas.incident_schemas import IncidentReport
from app.utils.db import get_dynamodb_table
from app.core.auth import get_current_user

import boto3
import uuid
from decimal import Decimal
from boto3.dynamodb.conditions import Key

incident_table = get_dynamodb_table("incidents")

router = APIRouter(prefix="/incident", tags=["incident"])

@router.post("/report")
async def report_incident(
    data: IncidentReport,
    current_user: str = Depends(get_current_user)
):
    incident_id = f"incident_{uuid.uuid4().hex}"

    item = {
        "incident_id": incident_id,
        "email": current_user,
        "incident_type": data.incident_type,
        "description": data.description,
        "location": {
            "latitude": Decimal(str(data.location.latitude)),
            "longitude": Decimal(str(data.location.longitude))
        },
        "timestamp": data.timestamp.isoformat(),
        "resolved": False
    }

    incident_table.put_item(Item=item)

    return {
        "message": "Incident reported successfully",
        "incident_id": incident_id
    }


@router.get("/history")
async def get_incident_history(
    current_user: str = Depends(get_current_user)
):
    try:
        response = incident_table.query(
            IndexName="email-index",  # GSI required
            KeyConditionExpression=Key("email").eq(current_user)
        )

    except incident_table.meta.client.exceptions.ResourceNotFoundException:
        raise HTTPException(
            status_code=500,
            detail="Incident table or email-index not found"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    items = response.get("Items", [])

    return {
        "incidents": items
    }

@router.get("/{incident_id}")
async def get_incident_by_id(
    incident_id: str = Path(...),
    current_user: str = Depends(get_current_user)
):
    try:
        response = incident_table.get_item(
            Key={"incident_id": incident_id}
        )

        item = response.get("Item")
        if not item:
            raise HTTPException(status_code=404, detail="Incident not found")

        # 🔐 Prevent access to others' incidents
        if item["email"] != current_user:
            raise HTTPException(status_code=403, detail="Access denied")

        return item

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching incident: {str(e)}"
        )
