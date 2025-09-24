# routes/register.py
from fastapi import APIRouter
from models import AgentCard
from storage import storage

router = APIRouter()

@router.post("/register")
def register_agent(card: AgentCard):
    storage.register(card)
    return {"message": f"{card.name} registered."}

