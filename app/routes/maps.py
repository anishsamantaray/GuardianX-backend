from fastapi import APIRouter, Query
import httpx
import os
from dotenv import load_dotenv
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