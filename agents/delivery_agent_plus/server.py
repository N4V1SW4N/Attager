"""FastAPI server exposing DeliveryAgentPlus response."""
from __future__ import annotations

from typing import Any, Optional, Union

from fastapi import FastAPI
from pydantic import BaseModel
from uuid import uuid4

from .agent import root_agent

app = FastAPI(title="Delivery Agent Plus", description="향상된 배송 안내 POC")


class JsonRpcRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: Optional[Union[int, str]] = None
    method: Optional[str] = None
    params: Optional[dict[str, Any]] = None


def _jsonrpc_response(req_id: Optional[Union[int, str]]) -> dict[str, Any]:
    message_text = root_agent.handle()
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {
            "kind": "message",
            "role": "agent",
            "messageId": uuid4().hex,
            "parts": [
                {
                    "kind": "text",
                    "text": message_text,
                }
            ],
        },
    }


@app.post("/")
async def handle_jsonrpc_root(payload: JsonRpcRequest) -> dict[str, Any]:
    return _jsonrpc_response(payload.id)


@app.post("/jsonrpc")
async def handle_jsonrpc(payload: JsonRpcRequest) -> dict[str, Any]:
    return _jsonrpc_response(payload.id)


@app.get("/message")
async def fetch_message() -> dict[str, str]:
    return {"message": root_agent.handle()}


@app.get("/")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
