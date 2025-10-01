# customer_agent.py
import asyncio
import os
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.models.lite_llm import LiteLlm
from google.genai import types

# CustomerTool 불러오기
from .customer_tool import CustomerTool

# --- 1. Agent 정의 ---
LITELLM_MODEL = os.getenv("LITELLM_MODEL", "gemini-2.5-flash")
customer_tool = CustomerTool()

root_agent = LlmAgent(
    model=LiteLlm(model=LITELLM_MODEL),
    name="CustomerAgent",
    description="고객 이름으로 기본 정보와 구매 내역을 조회하는 에이전트",
    instruction="""너는 고객 관리 에이전트다.
    - 사용자가 고객 이름을 말하면 반드시 CustomerTool.query(name) 툴을 호출해야 한다.
    - 고객 기본 정보(이름, 나이, 주소, 연락처)와 구매 내역(상품명, 수량, 구매일자, 가격)을 Markdown 형식으로 정리해서 보여줘.
    - 임의로 정보를 만들어내지 말고, 반드시 툴의 응답만 사용해라.
    """,
    tools=[customer_tool.query],
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
