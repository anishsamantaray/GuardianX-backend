from fastapi import APIRouter, Query, Depends
import httpx
import os
from dotenv import load_dotenv

from app.core.auth import get_current_user
from app.utils.maps import (
    get_user_home_coordinates,
    get_distance_from_home
)
from app.utils.redis_cache import get_cache, set_cache
from app.utils.redis_circuit_breaker import execute_with_breaker

load_dotenv()
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

router = APIRouter(prefix="/maps", tags=["maps"])


@router.get("/autocomplete")
async def autocomplete(
    input: str = Query(...),
    _: str = Depends(get_current_user)
):
    url = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
    params = {"input": input, "key": GOOGLE_MAPS_API_KEY}

    async def call_google_maps():
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=5.0)
            response.raise_for_status()
            return response.json()

    try:
        data = await execute_with_breaker(
            "google_maps_autocomplete",
            call_google_maps
        )
        return [
            {
                "description": item["description"],
                "place_id": item["place_id"]
            }
            for item in data.get("predictions", [])
        ]

    except Exception as e:
        return {"error": f"Google Maps (autocomplete) unavailable: {str(e)}"}


@router.get("/details")
async def place_details(
    place_id: str = Query(...),
    _: str = Depends(get_current_user)
):
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {"place_id": place_id, "key": GOOGLE_MAPS_API_KEY}

    async def call_google_maps_details():
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=5.0)
            response.raise_for_status()
            return response.json()

    try:
        data = await execute_with_breaker(
            "google_maps_details",
            call_google_maps_details
        )

        result = data.get("result", {})
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

        return {
            "line1": result.get("formatted_address"),
            "line2": "",
            "city": city,
            "state": state,
            "pincode": pincode,
            "latitude": location.get("lat"),
            "longitude": location.get("lng"),
        }

    except Exception as e:
        return {"error": f"Google Maps (details) unavailable: {str(e)}"}


@router.get("/distance-from-home")
async def get_distance_from_home_endpoint(
    current_lat: float = Query(...),
    current_lng: float = Query(...),
    current_user: str = Depends(get_current_user)
):
    rounded_lat = round(current_lat, 4)
    rounded_lng = round(current_lng, 4)

    cache_key = f"cache:distance:{current_user}:{rounded_lat}:{rounded_lng}"

    cached = await get_cache(cache_key)
    if cached:
        return cached

    home_lat, home_lng = await get_user_home_coordinates(current_user)
    distance = await get_distance_from_home(
        home_lat,
        home_lng,
        current_lat,
        current_lng
    )

    response_data = {
        "home_location": {
            "latitude": home_lat,
            "longitude": home_lng
        },
        "current_location": {
            "latitude": current_lat,
            "longitude": current_lng
        },
        "distance_from_home": distance,
    }

    await set_cache(cache_key, response_data, ttl=3600)

    return response_data


@router.get("/reverse-geocode")
async def reverse_geocode(
    lat: float = Query(...),
    lng: float = Query(...),
    _: str = Depends(get_current_user)
):
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"latlng": f"{lat},{lng}", "key": GOOGLE_MAPS_API_KEY}

    async def call_google_reverse_geocode():
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=5.0)
            response.raise_for_status()
            return response.json()

    try:
        data = await execute_with_breaker(
            "google_maps_reverse",
            call_google_reverse_geocode
        )

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

        return {
            "line1": result.get("formatted_address"),
            "line2": "",
            "city": city,
            "state": state,
            "pincode": pincode,
            "latitude": location.get("lat"),
            "longitude": location.get("lng"),
        }

    except Exception as e:
        return {"error": f"Google Maps (reverse geocode) unavailable: {str(e)}"}
