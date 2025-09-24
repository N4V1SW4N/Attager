# routes/unregister.py
from fastapi import APIRouter, HTTPException
from storage import storage

router = APIRouter()

@router.delete("/agents/{name}")
def unregister_agent(name: str):
    if not storage.get(name):
        raise HTTPException(status_code=404, detail="Agent not found")
    storage.unregister(name)
    return {"message": f"{name} unregistered."}

