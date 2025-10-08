# Bridge Agent / Orchestrator 가이드

## 🚀 빠른 시작 (Docker)
1. **사전 준비**
   - Docker 24.x 이상과 Docker Compose 플러그인이 설치되어 있어야 합니다.
   - (선택) 로컬 LLM 폴백용 Ollama가 `host.docker.internal`로 접근 가능해야 합니다.
2. **환경 변수 설정**
   - 프로젝트 루트에 `.env` 파일을 만들고 아래 값을 필요한 만큼 채웁니다.
   ```env
   GOOGLE_API_KEY=""             # (선택) Google AI Studio Key
   GOOGLE_GENAI_USE_VERTEXAI=FALSE
   USE_GEMINI=true                # Gemini를 우선 사용할지 여부
   FALLBACK_TO_LOCAL=true         # Gemini 실패 시 로컬 LLM(Ollama) 사용
   OLLAMA_HOST=host.docker.internal  # Docker→호스트 Ollama 접근 시 권장값
   ```
3. **컨테이너 빌드 및 실행**
   ```bash
   docker compose up -d --build
   ```
4. **접속 포트**
   - Bridge Agent: <http://localhost:10007>
   - Logistics Orchestrator: <http://192.168.10.10:10000>
   - Customer Orchestrator: <http://192.168.20.10:10005>

> ℹ️ 로컬 환경에서 오케스트레이터를 직접 띄우지 않는 경우, 위 두 오케스트레이터 주소는 원격 환경(사내 네트워크 등)에 존재해야 합니다. 필요에 따라 `bridge_agent/agent.py`의 `ORCHESTRATORS` 상수를 수정해 주세요.

## 🛠️ 로컬 개발 실행 (선택)
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Bridge Agent (기본: 0.0.0.0:10007)
python -m bridge_agent --host 0.0.0.0 --port 10007

# Bridge Orchestrator (기본: 127.0.0.1:10000)
python -m bridge_orchestrator
```

- 로컬 오케스트레이터는 `agent_card/` 디렉토리의 JSON 파일을 읽어 다른 원격 에이전트를 호출합니다.
- `.env` 파일이 없으면 `utils/model_config.py`가 자동으로 환경 변수를 읽어 Gemini 혹은 로컬 LLM을 선택합니다.

## 🔁 Bridge Agent 라우팅 개요
- `bridge_agent`는 LLM이 사용자의 의도를 분류하여 물류/고객 오케스트레이터 중 하나로 라우팅합니다.
- 오케스트레이터 주소는 `bridge_agent/agent.py`의 `ORCHESTRATORS` 상수에서 관리합니다.
- 모델 선택 및 폴백 로직은 `utils/model_config.py`를 참고하세요.
- 한 번의 `docker compose up`으로 Agent와 Orchestrator 컨테이너를 동시에 실행할 수 있습니다.

## 🔍 유용한 확인 명령
- `docker compose logs -f bridge_agent` : 라우팅 및 원격 호출 로그 확인
- `docker compose ps` : 컨테이너 상태 확인
- `curl http://localhost:10007/health` : (엔드포인트 제공 시) Agent 상태 점검

## 🧪 추가 팁
- 새 Agent Card를 등록하려면 `agent_card/*.json` 파일을 추가하고, 필요한 경우 `AGENT_CARD_DIR` 환경 변수를 수정합니다.
- 테스트 작성 시 `pytest`와 `pytest-asyncio`를 활용할 수 있습니다.
