import os

import uvicorn
from fastapi import Depends, FastAPI, Request
from fastapi.responses import Response

from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from utils.auth_guard import auth_guard

from .agent import root_agent as item_agent
from .agent_executor import ADKAgentExecutor

DEFAULT_HOST = os.getenv("AGENT_HOST", "0.0.0.0")
DEFAULT_PORT = int(os.getenv("AGENT_PORT", "10002"))


def _build_server(inhost: str, inport: int) -> A2AStarletteApplication:
    agent_card = AgentCard(
        name="Item Agent",
        description=item_agent.description,
        url=f"http://{inhost}:{inport}",
        version="1.0.0",
        defaultInputModes=["text", "text/plain"],
        defaultOutputModes=["text", "text/plain"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[
            AgentSkill(
                id="item_agent",
                name="manage item operations",
                description="Handle item data retrieval, inventory tracking, and item management",
                tags=["item", "inventory", "product"],
                examples=[
                    "Read item details for ITEM001",
                    "Track item inventory",
                    "Check product availability",
                    "Get item status",
                ],
            )
        ],
    )

    request_handler = DefaultRequestHandler(
        agent_executor=ADKAgentExecutor(agent=item_agent),
        task_store=InMemoryTaskStore(),
    )
    return A2AStarletteApplication(agent_card=agent_card, http_handler=request_handler)


def _create_app(server: A2AStarletteApplication) -> FastAPI:
    fastapi_app = FastAPI()

    @fastapi_app.post("/jsonrpc")
    async def jsonrpc_endpoint(request: Request, _claims=Depends(auth_guard)) -> Response:
        return await server._handle_requests(request)

    @fastapi_app.get("/.well-known/agent-card.json")
    async def agent_card_endpoint(request: Request) -> Response:
        return await server._handle_get_agent_card(request)

    @fastapi_app.get("/.well-known/agent.json")
    async def deprecated_agent_card_endpoint(request: Request) -> Response:
        return await server._handle_get_agent_card(request)

    return fastapi_app


app = _create_app(_build_server(DEFAULT_HOST, DEFAULT_PORT))


def main(inhost: str | None = None, inport: int | None = None) -> None:
    inhost = inhost or DEFAULT_HOST
    inport = inport or DEFAULT_PORT
    server = _build_server(inhost, inport)
    app = _create_app(server)
    uvicorn.run(app, host=inhost, port=inport)


if __name__ == "__main__":
    main()
