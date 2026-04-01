import re
import httpx
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import WatchlistItem
from database.utils import serialize

router = APIRouter()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-AU,en;q=0.9",
}


def _extract_og(html: str, prop: str) -> Optional[str]:
    patterns = [
        rf'<meta[^>]+property=["\']og:{prop}["\'][^>]+content=["\']([^"\']+)["\']',
        rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:{prop}["\']',
    ]
    for p in patterns:
        m = re.search(p, html, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return None


def fetch_og_data(url: str) -> dict:
    try:
        r = httpx.get(url, headers=HEADERS, follow_redirects=True, timeout=10)
        r.raise_for_status()
        html = r.text
        return {
            "og_title":       _extract_og(html, "title"),
            "og_image":       _extract_og(html, "image"),
            "og_description": _extract_og(html, "description"),
        }
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Listing URL returned {e.response.status_code}")
    except httpx.RequestError:
        # Network error — silently return empty rather than failing the whole request
        return {"og_title": None, "og_image": None, "og_description": None}


class WatchlistIn(BaseModel):
    listing_url:   Optional[str]   = None
    address:       str
    suburb:        Optional[str]   = None
    state:         Optional[str]   = None
    asking_price:  Optional[float] = None
    bedrooms:      Optional[int]   = None
    bathrooms:     Optional[float] = None
    parking:       Optional[int]   = None
    land_size:     Optional[int]   = None
    property_type: Optional[str]   = None
    status:        str             = "watching"
    notes:         Optional[str]   = None


@router.get("/watchlist")
def list_watchlist(db: Session = Depends(get_db)):
    items = db.query(WatchlistItem).order_by(WatchlistItem.created_at.desc()).all()
    return [serialize(i) for i in items]


@router.post("/watchlist", status_code=201)
def create_watchlist(data: WatchlistIn, db: Session = Depends(get_db)):
    payload = data.model_dump(exclude_none=True)
    if data.listing_url:
        og = fetch_og_data(data.listing_url)
        payload.update({k: v for k, v in og.items() if v})
    item = WatchlistItem(**payload)
    db.add(item)
    db.commit()
    db.refresh(item)
    return serialize(item)


@router.put("/watchlist/{item_id}")
def update_watchlist(item_id: str, data: WatchlistIn, db: Session = Depends(get_db)):
    item = db.query(WatchlistItem).filter(WatchlistItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    for key, val in data.model_dump(exclude_none=True).items():
        setattr(item, key, val)
    db.commit()
    db.refresh(item)
    return serialize(item)


@router.delete("/watchlist/{item_id}", status_code=204)
def delete_watchlist(item_id: str, db: Session = Depends(get_db)):
    item = db.query(WatchlistItem).filter(WatchlistItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(item)
    db.commit()


@router.post("/watchlist/{item_id}/refresh-preview")
def refresh_preview(item_id: str, db: Session = Depends(get_db)):
    item = db.query(WatchlistItem).filter(WatchlistItem.id == item_id).first()
    if not item or not item.listing_url:
        raise HTTPException(status_code=404, detail="No URL to fetch")
    og = fetch_og_data(item.listing_url)
    for key, val in og.items():
        setattr(item, key, val)
    db.commit()
    db.refresh(item)
    return serialize(item)
