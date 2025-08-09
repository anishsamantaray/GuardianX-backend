import time
from boto3.dynamodb.conditions import Key, Attr
from fastapi import HTTPException

from app.utils.db import get_dynamodb_table

requests_table = get_dynamodb_table("ally_requests")
users_table = get_dynamodb_table("users")


def check_existing_request(from_email: str, to_email: str):
    response = requests_table.get_item(
        Key={"to_email": to_email, "from_email": from_email}
    )
    return "Item" in response


def create_ally_request(from_email: str, to_email: str):
    if from_email == to_email:
        raise HTTPException(status_code=400, detail="Cannot send request to yourself.")

    # quick duplicate check (cheap read)
    if check_existing_request(from_email, to_email):
        raise HTTPException(status_code=400, detail="Request already sent.")

    # idempotent write: if the item already exists, DynamoDB will throw ConditionalCheckFailedException
    try:
        requests_table.put_item(
            Item={
                "to_email": to_email,
                "from_email": from_email,
                "status": "pending",
                "timestamp": int(time.time()),
            },
            ConditionExpression="attribute_not_exists(to_email) AND attribute_not_exists(from_email)",
        )
    except Exception as e:
        # If two requests race each other, this will catch the conditional failure
        raise HTTPException(status_code=400, detail="Request already sent.") from e


def _collect_all_pages(**kwargs):
    """Helper: query all pages (handles LastEvaluatedKey)."""
    items = []
    resp = requests_table.query(**kwargs)
    items.extend(resp.get("Items", []))
    while "LastEvaluatedKey" in resp:
        kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]
        resp = requests_table.query(**kwargs)
        items.extend(resp.get("Items", []))
    return items


def get_sent_pending_requests(from_email: str):
    """
    Requires GSI: from_email-index (PK: from_email)
    Returns [{ to_email, timestamp }] for status == 'pending'
    """
    items = _collect_all_pages(
        IndexName="from_email-index",
        KeyConditionExpression=Key("from_email").eq(from_email),
        FilterExpression=Attr("status").eq("pending"),
        ProjectionExpression="to_email, #ts, #st",
        ExpressionAttributeNames={"#ts": "timestamp", "#st": "status"},
    )
    return [{"to_email": it["to_email"], "timestamp": it["timestamp"]} for it in items]


def get_pending_requests(to_email: str):
    """
    Returns [{ from_email, timestamp }] for status == 'pending'
    """
    items = _collect_all_pages(
        KeyConditionExpression=Key("to_email").eq(to_email),
        FilterExpression=Attr("status").eq("pending"),
        ProjectionExpression="from_email, #ts, #st",
        ExpressionAttributeNames={"#ts": "timestamp", "#st": "status"},
    )
    return [{"from_email": it["from_email"], "timestamp": it["timestamp"]} for it in items]


def respond_to_ally_request(to_email: str, from_email: str, response: str):
    # Check if request exists
    existing = requests_table.get_item(Key={"to_email": to_email, "from_email": from_email})
    if "Item" not in existing:
        raise HTTPException(status_code=404, detail="Request not found")

    # Update ally_requests table with new status
    requests_table.update_item(
        Key={"to_email": to_email, "from_email": from_email},
        UpdateExpression="SET #s = :r",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":r": response},
    )

    if response == "accepted":
        # Add each other as allies (dedupe in app; keep list type)
        for user_email, other_email in [(to_email, from_email), (from_email, to_email)]:
            user = users_table.get_item(Key={"email": user_email}).get("Item", {}) or {}
            current_allies = user.get("allies", [])
            if other_email not in current_allies:
                current_allies.append(other_email)
                users_table.update_item(
                    Key={"email": user_email},
                    UpdateExpression="SET allies = :a",
                    ExpressionAttributeValues={":a": current_allies},
                )


def get_accepted_allies(email: str) -> list[str]:
    response = users_table.get_item(Key={"email": email})
    item = response.get("Item")

    if not item:
        raise HTTPException(status_code=404, detail="User not found")

    return item.get("allies", [])
