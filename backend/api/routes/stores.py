from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_session

router = APIRouter(prefix="/stores", tags=["Stores"])


class StoreCreateSchema(BaseModel):
    name: str
    aisle_order: Optional[Dict[str, Any]] = None


class StoreUpdateSchema(BaseModel):
    name: Optional[str] = None
    aisle_order: Optional[Dict[str, Any]] = None


@router.get("/")
def list_stores(session: Session = Depends(get_session)):
    """List available stores (e.g., King Soopers, Whole Foods)."""
    return {"status": "ok", "stores": []}


@router.post("/")
def create_store(payload: StoreCreateSchema, session: Session = Depends(get_session)):
    """Add a new store entry."""
    return {"status": "created", "name": payload.name}


@router.patch("/{store_id}")
def update_store(
    store_id: int, 
    payload: StoreUpdateSchema, 
    session: Session = Depends(get_session)
):
    """Update store details or aisle order configuration."""
    return {"status": "updated", "store_id": store_id}


@router.delete("/{store_id}")
def delete_store(store_id: int, session: Session = Depends(get_session)):
    """Remove a store record."""
    return {"status": "deleted", "store_id": store_id}