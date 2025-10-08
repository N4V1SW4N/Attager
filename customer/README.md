## 🚀 빠른 시작 - Customer VM (192.168.20.10)

customer VM(192.168.20.10)에서 프로젝트를 다운로드한 뒤 `customer` 폴더로 이동하세요. 아래 순서대로 실행하면 바로 테스트할 수 있습니다.

1. 환경 변수 설정(.env)
   - 루트 경로에 `.env` 파일을 만들고 아래 값을 입력합니다.
   ```
   GOOGLE_API_KEY="your_google_api_key_here"
   GOOGLE_GENAI_USE_VERTEXAI=FALSE
   USE_GEMINI=true
   FALLBACK_TO_LOCAL=true
   ```
   - Google AI Studio(또는 Vertex)에서 발급받은 실제 키로 `GOOGLE_API_KEY` 값을 교체하세요.
   - Gemini API Key가 없다면 `USE_GEMINI=false`로, 로컬 모델을 사용하지 않을 경우 `FALLBACK_TO_LOCAL=false`로 조정합니다.

2. Docker 실행
   ```
   docker compose up -d --build
   ```

3. (선택) 가상환경 및 의존성 설치(로컬 실행 시)
   ```
   uv venv
   source .venv/bin/activate
   uv pip install -r requirements.txt
   ```

4. ADK Web 실행
   ```
   adk web --port 8001
   ```

5. 브라우저 접속 및 테스트
   - http://localhost:8001 접속 후 아래와 같이 입력해 확인해 보세요.
   - 예) "홍길동 고객의 정보를 알려줘"


## Customer Orchestrator & Customer Agent 

### 개요
- 포함 서비스:
  - agent-registry (백엔드, 포트 8000)
  - agent-registry-frontend (프론트엔드, 포트 3000)
  - customer-agent (A2A 에이전트, 포트 10006)
  - customer-orchestrator (오케스트레이터, 포트 10005)
- 루트의 `docker-compose.yml`로 한 번에 빌드/실행합니다.

### 개별 실행(로컬)
- Orchestrator 실행
  ```bash
  # (선택) 가상환경 활성화
  source .venv/bin/activate

  python customer_orchestrator/__main__.py --host 0.0.0.0 --port 10005
  ```

- Customer Agent 실행
  ```bash
  # (선택) 가상환경 활성화
  source .venv/bin/activate

  python -m customer_agent --host 0.0.0.0 --port 10006
  ```

### 쉘 스크립트로 실행(동시에 구동)
- 최상위 폴더의 `run_all.sh` 사용
  ```bash
  # 권한 부여(최초 1회)
  chmod +x run_all.sh

  # 실행
  ./run_all.sh
  ```
  - GUI 터미널이 있으면 각 서비스가 새로운 터미널 창에서 실행됩니다.
  - GUI 터미널이 없으면 백그라운드로 실행되며 로그는 `customer_agent.out`, `orchestrator.out`에 저장됩니다.
