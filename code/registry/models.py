# models.py
from pydantic import BaseModel
from typing import List

class AgentCard(BaseModel):
    name: str
    description: str
    endpoint: str
    tags: List[str]

