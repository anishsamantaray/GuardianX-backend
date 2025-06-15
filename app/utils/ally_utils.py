import time
import boto3
from boto3.dynamodb.conditions import Key
from fastapi import HTTPException

dynamodb = boto3.resource("dynamodb", region_name="ap-south-1")
requests_table = dynamodb.Table("ally_requests")
users_table = dynamodb.Table("users")
def check_existing_request(from_email: str, to_email: str):
    response = requests_table.get_item(
        Key={"to_email": to_email, "from_email": from_email}
    )
    return "Item" in response

def create_ally_request(from_email: str, to_email: str):
    if from_email == to_email:
        raise HTTPException(status_code=400, detail="Cannot send request to yourself.")

    if check_existing_request(from_email, to_email):
        raise HTTPException(status_code=400, detail="Request already sent.")

    requests_table.put_item(
        Item={
            "to_email": to_email,
            "from_email": from_email,
            "status": "pending",
            "timestamp": int(time.time())
        }
    )

def respond_to_ally_request(to_email: str, from_email: str, response: str):
    # Check if request exists
    existing = requests_table.get_item(Key={"to_email": to_email, "from_email": from_email})
    if "Item" not in existing:
        raise HTTPException(status_code=404, detail="Request not found")

    # Update ally_requests table
    requests_table.update_item(
        Key={"to_email": to_email, "from_email": from_email},
        UpdateExpression="SET #s = :r",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":r": response}
    )

    if response == "accepted":
        # Update allies in users table for both
        for user_email, other_email in [(to_email, from_email), (from_email, to_email)]:
            user = users_table.get_item(Key={"email": user_email}).get("Item", {})
            current_allies = user.get("allies", [])
            if other_email not in current_allies:
                current_allies.append(other_email)

                users_table.update_item(
                    Key={"email": user_email},
                    UpdateExpression="SET allies = :a",
                    ExpressionAttributeValues={":a": current_allies}
                )

def get_pending_requests(to_email: str):
    response = requests_table.query(
        KeyConditionExpression=Key("to_email").eq(to_email)
    )
    items = response.get("Items", [])
    return [r for r in items if r["status"] == "pending"]