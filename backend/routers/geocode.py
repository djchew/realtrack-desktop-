import httpx
from fastapi import APIRouter, HTTPException

router = APIRouter()

NOMINATIM_HEADERS = {
    "User-Agent": "RealTrack-Desktop/1.0 (Australian property portfolio manager)",
    "Accept-Language": "en",
}


@router.get("/geocode")
async def geocode(q: str):
    """Proxy address autocomplete queries to Nominatim (AU only)."""
    if not q or len(q.strip()) < 3:
        return []
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            res = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params={
                    "q": q,
                    "format": "json",
                    "addressdetails": 1,
                    "limit": 5,
                    "countrycodes": "au",
                },
                headers=NOMINATIM_HEADERS,
            )
            res.raise_for_status()
            return res.json()
    except httpx.TimeoutException:
        return []
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Geocoding unavailable: {e}")
