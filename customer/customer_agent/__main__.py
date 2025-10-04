import click
import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from .agent import root_agent as customer_agent
from .agent_executor import ADKAgentExecutor

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 10008


def main(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
    # Agent card (metadata)
    agent_card = AgentCard(
        name="Customer Agent",
        description=customer_agent.description,
        url=f"http://{host}:{port}",
        version="1.0.0",
        defaultInputModes=["text", "text/plain"],
        defaultOutputModes=["text", "text/plain"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[
            AgentSkill(
                id="customer_agent",
                name="lookup customer info and purchases",
                description="Lookup customer profile and purchase history by customer name",
                tags=["customer", "crm", "orders"],
                examples=[
                    "홍길동 정보 보여줘",
                    "김철수 구매 내역",
                ],
            )
        ],
    )

    request_handler = DefaultRequestHandler(
        agent_executor=ADKAgentExecutor(
            agent=customer_agent,
        ),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )

    uvicorn.run(server.build(), host=host, port=port)


@click.command()
@click.option("--host", "host", default=DEFAULT_HOST)
@click.option("--port", "port", default=DEFAULT_PORT)
def cli(host: str, port: int):
    main(host, port)


if __name__ == "__main__":
    main()
