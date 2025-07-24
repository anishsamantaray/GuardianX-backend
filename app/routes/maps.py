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
    params = {"input": input, "key": GOOGLE_MAPS_API_KEY}

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        data = response.json()

        predictions = [
            {
                "description": item["description"],
                "place_id": item["place_id"]
            }
            for item in data.get("predictions", [])
        ]
        return predictions

@router.get("/details")
async def place_details(place_id: str = Query(...)):
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "key": GOOGLE_MAPS_API_KEY
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        data = response.json()
        result = data.get("result", {})
        address_components = result.get("address_components", [])

        city = next(
            (c["long_name"] for c in address_components if "locality" in c["types"]),
            None
        )

        # Prioritize administrative_area_level_1, then fallback in order
        state = None
        for level in range(1, 6):
            state = next(
                (
                    c["long_name"]
                    for c in address_components
                    if f"administrative_area_level_{level}" in c["types"]
                ),
                None
            )
            if state:
                break

        pincode = next(
            (c["long_name"] for c in address_components if "postal_code" in c["types"]),
            None
        )

        location = result.get("geometry", {}).get("location", {})
        lat = location.get("lat")
        lng = location.get("lng")

        return {
            "line1": result.get("formatted_address"),
            "line2": "",
            "city": city,
            "state": state,
            "pincode": pincode,
            "latitude": lat,
            "longitude": lng
        }


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

@router.get("/reverse-geocode")
async def reverse_geocode(
    lat: float = Query(...),
    lng: float = Query(...)
):
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "latlng": f"{lat},{lng}",
        "key": GOOGLE_MAPS_API_KEY
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        data = response.json()

    # Pick the first result (most relevant)
    results = data.get("results", [])
    if not results:
        return {"error": "No results found"}

    result = results[0]
    address_components = result.get("address_components", [])

    city = next(
        (c["long_name"] for c in address_components if "locality" in c["types"]),
        None
    )

    state = None
    for level in range(1, 6):
        state = next(
            (
                c["long_name"]
                for c in address_components
                if f"administrative_area_level_{level}" in c["types"]
            ),
            None
        )
        if state:
            break

    pincode = next(
        (c["long_name"] for c in address_components if "postal_code" in c["types"]),
        None
    )

    location = result.get("geometry", {}).get("location", {})
    latitude = location.get("lat")
    longitude = location.get("lng")

    return {
        "line1": result.get("formatted_address"),
        "line2": "",
        "city": city,
        "state": state,
        "pincode": pincode,
        "latitude": latitude,
        "longitude": longitude
    }
