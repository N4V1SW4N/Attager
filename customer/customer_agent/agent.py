# customer_agent.py
import asyncio
import os
import logging
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.models.lite_llm import LiteLlm
from google.genai import types
from google.adk.tools import FunctionTool
import sys
from dotenv import load_dotenv

# Ensure project root is importable for utils
sys.path.insert(0, '.')

# Load local .env if present
load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
try:
    from utils.model_config import get_model_with_fallback
except Exception:
    # Final local fallback if utils import fails
    ollama_host = os.getenv("OLLAMA_HOST", "localhost")

    def get_model_with_fallback():
        return LiteLlm(
            model="ollama_chat/gpt-oss:20b",
            api_base=f"http://{ollama_host}:11434",
            temperature=0.7,
        )

# CustomerTool 불러오기
from .customer_tool import CustomerTool

# --- 1. Agent 정의 ---
customer_tool = CustomerTool()

# Gemini 우선, 실패시 로컬 LLM 사용
try:
    model = get_model_with_fallback()
    logger.info(f"CustomerAgent 모델 설정 완료: {type(model).__name__ if hasattr(model, '__class__') else model}")
except Exception as e:
    logger.error(f"CustomerAgent 모델 설정 실패: {e}")
    # 최후의 fallback
    ollama_host = os.getenv("OLLAMA_HOST", "localhost")
    model = LiteLlm(
        model="ollama_chat/gpt-oss:20b",
        api_base=f"http://{ollama_host}:11434",
        temperature=0.7,
    )
    logger.info("CustomerAgent 최후 fallback으로 로컬 LLM 사용")

def query_customer(name: str):
    return customer_tool.query(name)

root_agent = LlmAgent(
    model=model,
    name="CustomerAgent",
    description="고객 이름으로 기본 정보와 구매 내역을 조회하는 에이전트 - Gemini/Local LLM hybrid",
    instruction="""너는 고객 관리 에이전트다.
    - 사용자가 고객 이름을 말하면 반드시 query_customer 툴을 호출해야 한다.
    - 고객 기본 정보(이름, 나이, 주소, 연락처)와 구매 내역(상품명, 수량, 구매일자, 가격)을 Markdown 형식으로 정리해서 보여줘.
    - 임의로 정보를 만들어내지 말고, 반드시 툴의 응답만 사용해라.
    """,
    tools=[FunctionTool(query_customer)],
)

# --- 2. Runner + 세션 서비스 ---
APP_NAME = "simple_customer_app"
USER_ID = "user1"
SESSION_ID = "sess1"

session_service = InMemorySessionService()
runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)

# --- 3. 실행 ---
async def main():
    await session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
    )

    print(">>> User Input: 홍길동 구매 내역 보여줘")
    final_response = "응답 없음"
    user_message = types.Content(
        role="user",
        parts=[types.Part(text="홍길동 구매 내역 보여줘")]
    )

    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=user_message,
    ):
        print(f"[DEBUG EVENT] {event}")  # 이벤트 구조 확인

        if event.content and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    final_response = part.text
    
    if not final_response.strip():
        final_response = "응답 없음"

    print(f"<<< Agent Response: {final_response}")


if __name__ == "__main__":
    asyncio.run(main())
