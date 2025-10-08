import os
import logging
import sys
from typing import List, Dict
import httpx
import uuid

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import FunctionTool
from google.adk.tools.tool_context import ToolContext
from a2a.types import AgentCard, Message, Role, Part, TextPart, MessageSendParams, SendMessageRequest, AgentCapabilities, AgentSkill
from a2a.client import A2AClient
from a2a.client.errors import A2AClientHTTPError

# Docker 환경에서는 현재 디렉토리를 PYTHONPATH에 추가
sys.path.insert(0, ".")
from utils.model_config import get_model_with_fallback

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# --- 연결 대상 오케스트레이터 주소 ---
ORCHESTRATORS = {
    "logistics_orchestrator": "http://192.168.10.10:10000",
    "customer_orchestrator": "http://192.168.20.10:10005",
}

# --- 1. AgentCard 로더 ---
async def load_agent_cards(tool_context: ToolContext) -> List[str]:
    """
    두 오케스트레이터(logistics/customer)의 AgentCard를 구성해 state에 저장하고,
    오케스트레이터 이름 리스트를 반환합니다.
    """
    cards: Dict[str, AgentCard] = {}

    for name, url in ORCHESTRATORS.items():
        try:
            card = AgentCard(
                name=name,
                description=f"Bridge target orchestrator: {name}",
                url=url,
                version="1.0.0",
                defaultInputModes=["text", "text/plain"],
                defaultOutputModes=["text", "text/plain"],
                capabilities=AgentCapabilities(streaming=True),
                skills=[
                    AgentSkill(
                        id="route_to_orchestrator",
                        name="Route to team orchestrator",
                        description="Routes user requests to the appropriate team orchestrator",
                        tags=["routing", "orchestrator"],
                        examples=[
                            "배송 관련 질문이면 logistics 오케스트레이터로 전달",
                            "고객 정보 질문이면 customer 오케스트레이터로 전달",
                        ],
                    )
                ],
            )
            cards[name] = card
            logger.info("Registered orchestrator: %s (%s)", name, url)
        except Exception as e:
            logger.error("Failed to build AgentCard for orchestrator %s: %s", name, e)

    tool_context.state["cards"] = cards
    logger.info("Total registered orchestrators: %d", len(cards))
    return list(cards.keys())

# --- 2. Remote Agent 호출 ---
async def call_remote_agent(tool_context, agent_name: str, task: str):
    """
    원격 에이전트를 호출하는 함수
    """
    cards: dict[str, AgentCard] = tool_context.state.get("cards", {})
    card = cards.get(agent_name)
    if not card:
        return {"error": f"Agent {agent_name} not found. Available: {list(cards.keys())}"}

    target_url = getattr(card, "url", None)
    if not target_url:
        logger.warning("Agent card for '%s' has no URL. Card=%s", agent_name, card)
    else:
        logger.info("Calling remote agent '%s' at %s", agent_name, target_url)

    async with httpx.AsyncClient(timeout=30.0) as httpx_client:
        client = A2AClient(httpx_client=httpx_client, agent_card=card)

        message = Message(
            role=Role.user,
            parts=[Part(root=TextPart(text=task))],
            messageId=uuid.uuid4().hex,
        )
        send_params = MessageSendParams(message=message)
        request = SendMessageRequest(id=str(uuid.uuid4()), params=send_params)

        try:
            resp = await client.send_message(request)
            return resp.model_dump(mode="json", exclude_none=True)
        except (httpx.ConnectError, httpx.ReadTimeout, httpx.WriteTimeout, httpx.PoolTimeout) as e:
            logger.error("Network error calling agent '%s' at %s: %s", agent_name, target_url, e)
            return {
                "error": "network_error",
                "agent": agent_name,
                "url": target_url,
                "detail": str(e),
            }
        except A2AClientHTTPError as e:
            logger.error("A2A HTTP error calling agent '%s' at %s: %s", agent_name, target_url, e)
            return {
                "error": "a2a_http_error",
                "agent": agent_name,
                "url": target_url,
                "detail": str(e),
            }
        except Exception as e:
            logger.exception("Unexpected error calling agent '%s' at %s", agent_name, target_url)
            return {
                "error": "unexpected_error",
                "agent": agent_name,
                "url": target_url,
                "detail": str(e),
            }

# --- 3. 최종 결과 반환 ---
def return_result(tool_context: ToolContext, result: str) -> str:
    tool_context.state["final_result"] = result
    return result

# --- Root Agent 정의 ---
try:
    model = get_model_with_fallback()
    logger.info(f"모델 설정 완료: {type(model).__name__ if hasattr(model, '__class__') else model}")
except Exception as e:
    logger.error(f"모델 설정 실패: {e}")
    ollama_host = os.getenv("OLLAMA_HOST", "localhost")
    model = LiteLlm(
        model="ollama_chat/gpt-oss:20b",
        api_base=f"http://{ollama_host}:11434",
        temperature=0.7,
    )
    logger.info("Fallback: 로컬 LLM 사용")

root_agent = LlmAgent(
    name="bridge_agent",
    model=model,
    instruction=(
        "너는 Bridge Agent야.\n"
        "사용자의 요청 의도를 파악해 적합한 오케스트레이터(logistics/customer)를 선택해야 한다.\n"
        "'load_agent_cards'를 호출하면 두 오케스트레이터의 카드가 준비된다.\n"
        "오케스트레이터 주소는 logistics=192.168.10.10:10000, customer=192.168.20.10:10005 이다.\n"
        "'call_remote_agent'로 선택한 오케스트레이터에 질문을 전달하고,\n"
        "'return_result'로 최종 결과를 사용자에게 반환하라.\n"
    ),
    description="LLM 기반 Bridge Agent (routes to team orchestrators)",
    tools=[FunctionTool(load_agent_cards), FunctionTool(call_remote_agent), FunctionTool(return_result)],
)
