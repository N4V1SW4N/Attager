# customer_agent.py
import asyncio
import os
import json
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.models.lite_llm import LiteLlm


# --- 에이전트 카드 불러오기 ---
AGENT_CARD_PATH = os.path.join(os.path.dirname(__file__), "..", "agent_card", "customer_agent_card.json")

def load_agent_card(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

customer_agent_card_data = load_agent_card(AGENT_CARD_PATH)

# --- 1. Agent 정의 ---
LITELLM_MODEL = os.getenv("LITELLM_MODEL", "gemini-2.5-flash")

root_agent = LlmAgent(
    model=LiteLlm(model=LITELLM_MODEL),
    name=customer_agent_card_data["name"],
    description=customer_agent_card_data["description"],
    instruction="""어떤 질문을 받았을때 그 질문에 대해서는 00팀에 문의해주세요 라고 대답해야 한다.
    """,
    # tools=[customer_tool.query],
)

# --- 2. Runner + 세션 서비스 ---
APP_NAME = "bridge_agent_app"
USER_ID = "user1"
SESSION_ID = "sess1"

session_service = InMemorySessionService()
runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)

# --- 3. 실행 ---
async def main(user_message: str):
    await session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
    )

    print(">>> User Input: " + user_message)
    # final_response = "00팀에 문의해주세요."
    response = await runner.query(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
        message=user_message,
    )
    final_response = response.output.text
    print(f"<<< Agent Response: {final_response}")


if __name__ == "__main__":
    # 테스트용 입력
    asyncio.run(main("배송 언제 되는거야?"))
    asyncio.run(main("00고객 정보를 알려줘"))
