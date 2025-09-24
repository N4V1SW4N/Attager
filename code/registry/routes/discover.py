# routes/discover.py
from fastapi import APIRouter, HTTPException
from storage import storage

router = APIRouter()

@router.get("/agents")
def list_agents():
    return storage.list_all()

@router.get("/agents/{name}")
def get_agent(name: str):
    card = storage.get(name)
    if not card:
        raise HTTPException(status_code=404, detail="Agent not found")
    return card

