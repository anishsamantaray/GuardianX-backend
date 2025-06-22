from fastapi import APIRouter, Query
import httpx
import os
from dotenv import load_dotenv

from app.utils.maps import get_user_home_coordinates, get_distance_from_home

load_dotenv()
GOOGLE_MAPS_API_KEY=os.getenv('GOOGLE_PLACES_API_KEY')
router = APIRouter(prefix="/maps", tags=["maps"])

@router.get("/autocomplete")
async def autocomplete(input: str = Query(...)):
    url = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
    params = {
        "input": input,
        "key": GOOGLE_MAPS_API_KEY
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        return response.json()


@router.get("/details")
async def place_details(place_id: str = Query(...)):
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "key": GOOGLE_MAPS_API_KEY
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        return response.json()

@router.get("/distance-from-home")
async def get_distance_from_home_endpoint(
    email: str = Query(...),
    current_lat: float = Query(...),
    current_lng: float = Query(...)
):
    # Step 1: Get home coordinates
    home_lat, home_lng = await get_user_home_coordinates(email)

    # Step 2: Calculate distance
    distance = await get_distance_from_home(home_lat, home_lng, current_lat, current_lng)

    return {
        "email": email,
        "home_location": {"latitude": home_lat, "longitude": home_lng},
        "current_location": {"latitude": current_lat, "longitude": current_lng},
        "distance_from_home": distance
    }