import logging
import os

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
from dotenv import load_dotenv
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

# ✅ 브릿지용 root_agent와 Executor
from .agent import root_agent
from .agent_executor import CustomerExecutor  

load_dotenv()
logging.basicConfig()

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 10007


def main(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
    # API 키 확인 (필수 조건 아님 → 브릿지에서는 Gemini/로컬 LLM 모두 가능)
    if not os.getenv("GOOGLE_API_KEY") and os.getenv("GOOGLE_GENAI_USE_VERTEXAI") != "TRUE":
        logging.warning(
            "⚠️ GOOGLE_API_KEY가 없고 GOOGLE_GENAI_USE_VERTEXAI도 활성화되지 않음. "
            "로컬 LLM fallback을 사용할 수 있습니다."
        )

    app_url = os.environ.get("APP_URL", f"http://{host}:{port}")

    # ✅ 브릿지 에이전트 카드
    agent_card = AgentCard(
        name="Bridge Orchestrator Agent",
        description="두 개 이상의 팀 레지스트리 서버에서 에이전트를 탐색하고 "
                    "사용자 요청에 맞는 에이전트를 선택/호출하는 오케스트레이션 에이전트",
        url=app_url,
        version="1.0.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[
            AgentSkill(
                id="bridge_orchestration",
                name="Orchestrate Multiple Agents",
                description="사용자의 요청을 해석하여 적합한 팀의 에이전트를 선택하고 호출하거나, "
                            "사용 가능한 모든 에이전트 목록을 안내합니다.",
                tags=["bridge", "orchestrator", "multi-agent"],
                examples=[
                    "홍길동 고객 정보를 알려줘",
                    "모든 에이전트를 보여줘",
                    "배송 관련 에이전트 알려줘",
                ],
            )
        ],
    )

    # ✅ Runner와 Executor
    runner = Runner(
        app_name=agent_card.name,
        agent=root_agent,
        artifact_service=InMemoryArtifactService(),
        session_service=InMemorySessionService(),
        memory_service=InMemoryMemoryService(),
    )
    agent_executor = CustomerExecutor(runner=runner, card=agent_card)

    # ✅ 요청 핸들러
    request_handler = DefaultRequestHandler(
        agent_executor=agent_executor,
        task_store=InMemoryTaskStore(),
    )

    a2a_app = A2AStarletteApplication(agent_card=agent_card, http_handler=request_handler)

    uvicorn.run(a2a_app.build(), host=host, port=port)


@click.command()
@click.option("--host", "host", default=DEFAULT_HOST)
@click.option("--port", "port", default=DEFAULT_PORT)
def cli(host: str, port: int):
    main(host, port)


if __name__ == "__main__":
    main()