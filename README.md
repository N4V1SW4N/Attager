# 🧭 Attager Multi-VM Deployment Guide

본 문서는 **Attager 시스템 (Bridge / Customer / Logistics)** 를 세 개의 Ubuntu VM 환경에 배포하는 과정을 설명합니다.

---

## 🏗️ 전체 구조

| VM 역할 | IP 주소 | 주요 서비스 | 브랜치 |
| --- | --- | --- | --- |
| Logistics VM | 192.168.10.10 | Agent Registry + Frontend | main |
| Customer VM | 192.168.20.10 | Customer Orchestrator + Customer Agent | Escalation |
| Bridge VM | 192.168.11.10 (예시) | Bridge Orchestrator + Bridge Agent | main |

---

## 🚀 Logistics VM (192.168.10.10)

- 메인 브랜치 클론

```bash
git clone -b main https://github.com/N4V1SW4N/Attager.git
cd Attager/agent-reg-new
```

- Docker 실행

```bash
docker compose up -d --build
```

- 서비스 포트
  - Agent Registry (Backend): http://localhost:8000
  - Agent Registry Frontend: http://localhost:3000

---

## 💼 Customer VM (192.168.20.10)

- Escalation 브랜치 클론

```bash
git clone -b Escalation https://github.com/N4V1SW4N/Attager.git
cd Attager/customer
```

- 환경 변수 설정 (`.env` 파일 생성)

```bash
GOOGLE_API_KEY=""
GOOGLE_GENAI_USE_VERTEXAI=FALSE
USE_GEMINI=true
FALLBACK_TO_LOCAL=false
```

- Docker 실행

```bash
docker compose up -d --build
```

- 상세 실행 가이드
  - `customer/README.md` 파일을 참조하세요. (ADK Web 실행, 테스트 방법 등 포함)

---

## 🌉 Bridge VM (예: 192.168.11.10)

- 메인 브랜치 클론

```bash
git clone -b main https://github.com/N4V1SW4N/Attager.git
cd Attager/bridge
```

- 환경 변수 설정 (`.env` 파일 생성)

```bash
GOOGLE_API_KEY=""
GOOGLE_GENAI_USE_VERTEXAI=FALSE
USE_GEMINI=true
FALLBACK_TO_LOCAL=true
OLLAMA_HOST=host.docker.internal
```

- Docker 실행

```bash
docker compose up -d --build
```

- 서비스 포트
  - Bridge Agent: http://localhost:10009
  - Bridge Orchestrator: http://localhost:10000

---

## 🧩 네트워크 연결 확인

Logistics → Bridge → Customer → Bridge → Logistics 순으로 통신이 필요합니다.

테스트 명령 예시:

```bash
# Logistics VM에서 Bridge VM 확인
ping 192.168.10.1

# Bridge VM에서 Customer VM 확인
ping 192.168.20.10

# Customer VM에서 Bridge VM 확인
ping 192.168.20.1

# Bridge VM에서 Logistics VM 확인
ping 192.168.20.10
```

연결이 불가능하면 vmnet 설정 또는 `ens33`, `ens37` 네트워크 인터페이스 IP를 확인하세요.

---

## 🧹 컨테이너 정리

- 모든 컨테이너 중지 및 삭제

```bash
docker compose down
```

- 이미지 재빌드 시

```bash
docker compose build --no-cache
```

---

## 📎 참고

- 각 폴더(`customer/`, `bridge/`, `agent-reg-new/`)에 개별 `README.md` 파일이 존재합니다.
- 세부 설정 및 ADK 실행 방법은 해당 폴더 내 README를 참조하세요.
- Google Gemini API Key 또는 Vertex AI ADC 설정이 필요합니다.
- Ollama를 사용하는 경우 로컬 환경에서 `11434` 포트를 열어둬야 합니다.
