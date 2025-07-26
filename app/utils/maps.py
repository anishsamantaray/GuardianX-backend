import httpx
import os

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

async def reverse_geocode(lat: float, lng: float) -> str:
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"latlng": f"{lat},{lng}", "key": GOOGLE_MAPS_API_KEY}

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        data = response.json()
        if data["results"]:
            return data["results"][0]["formatted_address"]
        return "Unknown location"


from app.utils.db import get_dynamodb_table
from fastapi import HTTPException

user_table = get_dynamodb_table("users")  # or "userDetails" based on your setup

async def get_user_home_coordinates(email: str) -> tuple[float, float]:
    response = user_table.get_item(Key={"email": email})
    user = response.get("Item")

    if not user or "home_address" not in user:
        raise HTTPException(status_code=404, detail="User or home address not found")

    home_address = user["home_address"]

    try:
        latitude = float(home_address.get("lat", {}).get("N"))
        longitude = float(home_address.get("long", {}).get("N"))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="Home lat or long is invalid or missing")

    return latitude, longitude

async def get_distance_from_home(home_lat: float, home_lng: float, current_lat: float, current_lng: float) -> str:
    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": f"{home_lat},{home_lng}",
        "destination": f"{current_lat},{current_lng}",
        "key": GOOGLE_MAPS_API_KEY,
        "mode": "driving"  # or "driving", "transit", "bicycling"
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        data = await response.json()
        if data["routes"]:
            return data["routes"][0]["legs"][0]["distance"]["text"]
        return "Distance not available"