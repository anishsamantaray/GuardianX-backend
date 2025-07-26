import httpx
import os
from app.utils.db import get_dynamodb_table
from fastapi import HTTPException
import math
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

user_table = get_dynamodb_table("users")  # or "userDetails" based on your setup

async def get_user_home_coordinates(email: str) -> tuple[float, float]:
    response = user_table.get_item(Key={"email": email})
    user = response.get("Item")

    if not user or "home_address" not in user:
        raise HTTPException(status_code=404, detail="User or home address not found")

    home_address = user["home_address"]

    try:
        latitude = float(home_address.get("lat"))
        longitude = float(home_address.get("long"))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="Home lat or long is invalid or missing")

    return latitude, longitude

def haversine(lat1, lon1, lat2, lon2):
    # Radius of Earth in kilometers
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)

    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance_km = R * c
    return round(distance_km, 2)

async def get_distance_from_home(home_lat: float, home_lng: float, current_lat: float, current_lng: float) -> str:
    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": f"{home_lat},{home_lng}",
        "destination": f"{current_lat},{current_lng}",
        "key": GOOGLE_MAPS_API_KEY,
        "mode": "driving"
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        data = response.json()

        if data.get("routes"):
            try:
                return data["routes"][0]["legs"][0]["distance"]["text"]
            except (KeyError, IndexError):
                pass  # fallback to haversine

    # Fallback manual calculation if no route found or error in response
    fallback_km = haversine(home_lat, home_lng, current_lat, current_lng)
    return f"{fallback_km} km"