## 🚀 빠른 시작 - Bridge Agent / Orchestrator

`bridge_agent`와 `bridge_orchestrator`를 Docker로 손쉽게 실행할 수 있습니다.

1. 환경 변수 설정(.env)
   - 루트 경로에 `.env` 파일을 만들고 아래 값을 입력합니다.
   ```
    GOOGLE_API_KEY=""             # (선택) Google AI Studio Key
    GOOGLE_GENAI_USE_VERTEXAI=FALSE
    USE_GEMINI=true                # Gemini 우선 사용 여부
    FALLBACK_TO_LOCAL=true         # 실패 시 로컬 LLM(Ollama)로 폴백
    OLLAMA_HOST=host.docker.internal  # 로컬 Ollama 사용 시 권장 값
   ```

2. Docker 실행
   ```
   docker compose up -d --build
   ```

3. 접근 포트
   - Bridge Agent: http://localhost:10009
   - Bridge Orchestrator: http://localhost:10000

4. (선택) 로컬 개발 실행
   ```
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt

   # Bridge Agent (기본: 0.0.0.0:10009)
   python -m bridge_agent --host 0.0.0.0 --port 10009

   # Bridge Orchestrator (기본: 127.0.0.1:10000)
   python -m bridge_orchestrator
   ```

## Bridge Orchestrator & Bridge Agent

### 개요
- 포함 서비스:
  - bridge_agent (A2A 에이전트, 포트 10009)
  - bridge_orchestrator (오케스트레이터, 포트 10000)
- 루트의 `docker-compose.yml`로 한 번에 빌드/실행합니다.

### 참고
- `bridge_agent`는 로컬 `agent_card/`의 JSON을 읽어 적합한 에이전트를 선택·호출합니다.
- `bridge_orchestrator`는 원격 레지스트리에서 에이전트 목록을 수집·호출하도록 설계되어 있습니다.
- 모델 선택/폴백 로직은 `utils/model_config.py`를 참고하세요.
