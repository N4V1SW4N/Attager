## Customer Orchestrator & Customer Agent - Run Guide

### 개요
- 포함 서비스:
  - agent-registry (백엔드, 포트 8000)
  - agent-registry-frontend (프론트엔드, 포트 3000)
  - customer-agent (A2A 에이전트, 포트 10008)
  - customer-orchestrator (오케스트레이터, 포트 10000)
- 루트의 `docker-compose.yml`로 한 번에 빌드/실행합니다.

### 준비물
- Docker, Docker Compose
- 선택: Google Gemini 사용 시 API 키 또는 Vertex AI ADC 설정

### 환경 변수 설정(.env)
루트 디렉토리에 `.env`를 생성해 아래 중 하나로 설정하세요.

#### 1) Google AI Studio API Key 사용(권장)
```
USE_GEMINI=true
FALLBACK_TO_LOCAL=true
GOOGLE_GENAI_USE_VERTEXAI=FALSE

# API 키 중 하나 이상 지정
GOOGLE_API_KEY=your_google_ai_studio_key
GEMINI_API_KEY=your_google_ai_studio_key

# 로컬 Ollama 사용 시 호스트 지정(옵션)
OLLAMA_HOST=host.docker.internal
```

#### 2) Vertex AI(ADC) 사용
```
USE_GEMINI=true
FALLBACK_TO_LOCAL=true
GOOGLE_GENAI_USE_VERTEXAI=TRUE

GOOGLE_APPLICATION_CREDENTIALS=/keys/sa.json
VERTEXAI_PROJECT=your-gcp-project-id
VERTEXAI_LOCATION=us-central1

# 필요 시 로컬 Ollama
OLLAMA_HOST=host.docker.internal
```
- 컨테이너에 자격증명 파일을 마운트해야 합니다:
  ```
  docker run ... -v /abs/path/keys/sa.json:/keys/sa.json ...
  ```

### 빌드 및 실행
루트에서 실행:
```
docker compose up -d --build
```

### 서비스 포트
- Agent Registry(API): http://localhost:8000
- Agent Registry Frontend: http://localhost:3000
- Customer Agent: http://localhost:10008
- Customer Orchestrator: http://localhost:10000

### 로그 확인
```
docker compose logs -f agent-registry

docker compose logs -f agent-registry-frontend

docker compose logs -f customer-agent

docker compose logs -f customer-orchestrator
```

### 중지/정리
```
docker compose down
```

### 문제 해결
- Vertex 자격증명 오류: `GOOGLE_GENAI_USE_VERTEXAI=FALSE`로 전환하고 `GOOGLE_API_KEY` 또는 `GEMINI_API_KEY`를 설정하세요. 또는 `GOOGLE_APPLICATION_CREDENTIALS`, `VERTEXAI_PROJECT`, `VERTEXAI_LOCATION`을 올바르게 지정하고 자격증명 파일을 컨테이너에 마운트하세요.
- 로컬 LLM(Ollama) Fallback: `FALLBACK_TO_LOCAL=true`일 때 `OLLAMA_HOST=host.docker.internal`로 설정하고 호스트에서 Ollama가 11434 포트로 동작 중인지 확인하세요.
- 의존성 변경 후: `requirements.txt` 수정 시 `docker compose build --no-cache`로 재빌드하세요.

### 로컬 실행(선택)
컨테이너 대신 customer-agent만 로컬에서 실행하려면:
```
python -m customer_agent --host 0.0.0.0 --port 10008
```
(사전에 `pip install -r requirements.txt` 필요)
