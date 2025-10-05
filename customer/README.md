## 🚀 빠른 시작 - Customer VM (192.168.20.10)

customer VM(192.168.20.10)에서 프로젝트를 다운로드한 뒤 `customer` 폴더로 이동하세요. 아래 순서대로 실행하면 바로 테스트할 수 있습니다.

1. 환경 변수 설정(.env)
   - 루트 경로에 `.env` 파일을 만들고 아래 값을 입력합니다.
   ```
  GOOGLE_API_KEY=""
  GOOGLE_GENAI_USE_VERTEXAI=FALSE
  USE_GEMINI=true
  FALLBACK_TO_LOCAL=false
   ```

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
  - customer-agent (A2A 에이전트, 포트 10008)
  - customer-orchestrator (오케스트레이터, 포트 10000)
- 루트의 `docker-compose.yml`로 한 번에 빌드/실행합니다.
