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
from a2a.types import AgentCard, Message, Role, Part, TextPart, MessageSendParams, SendMessageRequest
from a2a.client import A2AClient
from a2a.client.errors import A2AClientHTTPError

# Docker 환경에서는 현재 디렉토리를 PYTHONPATH에 추가
sys.path.insert(0, ".")
from utils.model_config import get_model_with_fallback

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# --- 레지스트리 서버 주소 ---
REGISTRY_URLS = {
    "logistics": "http://192.168.10.10:8000/agents",
    "customer": "http://192.168.20.10:8000/agents",
}

# --- 1. AgentCard 로더 ---
async def load_agent_cards(tool_context: ToolContext) -> List[str]:
    """
    원격 레지스트리 서버에서 에이전트 카드를 가져와 state에 저장,
    에이전트 이름 리스트 반환
    """
    cards: Dict[str, AgentCard] = {}

    for team, registry_url in REGISTRY_URLS.items():
        logger.info(f"Fetching agents from {team} registry at {registry_url}")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(registry_url)
                if response.status_code == 200:
                    agents = response.json()
                    logger.info(f"Loaded {len(agents)} agents from {team} registry")

                    for agent_data in agents:
                        try:
                            # ✅ dict → AgentCard 변환 (pydantic v1/v2 호환)
                            if hasattr(AgentCard, "model_validate"):   # pydantic v2
                                card = AgentCard.model_validate(agent_data)
                            else:  # pydantic v1
                                card = AgentCard.parse_obj(agent_data)

                            name = getattr(card, "name", None) or getattr(card, "url", None) or f"{team}_unknown"
                            cards[name] = card
                            logger.debug(
                                "Registered agent loaded: name=%s, url=%s, team=%s",
                                name,
                                getattr(card, "url", None),
                                team,
                            )
                        except Exception as e:
                            logger.error(f"Error parsing agent card from {team} registry: {e}")
                else:
                    logger.warning(f"Failed to fetch agents from {team} registry: {response.status_code}")
        except Exception as e:
            logger.error(f"Error connecting to {team} registry at {registry_url}: {e}")

    tool_context.state["cards"] = cards
    logger.info(f"Total loaded agents: {len(cards)}")
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
    name="bridge_orchestrator",
    model=model,
    instruction=(
        "너는 Bridge Orchestrator Agent야.\n"
        "사용자의 요청이 들어오면 두 레지스트리 서버에서 불러온 에이전트 목록을 확인해라.\n"
        "'load_agent_cards'를 이용해 192.168.10.20:8000 과 192.168.20.20:8000 의 에이전트 목록을 불러온다.\n"
        "'call_remote_agent'를 이용해 특정 에이전트에 작업을 위임할 수 있다.\n"
        "'return_result'를 호출해서 최종 결과를 반환해라.\n"
    ),
    description="LLM 기반 Bridge Orchestrator Agent (multi-agent coordination via registries)",
    tools=[FunctionTool(load_agent_cards), FunctionTool(call_remote_agent), FunctionTool(return_result)],
)
