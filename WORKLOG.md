# 작업 로그

## 2026-05-11

### 인프라 구성
- `docker-compose.yml` 작성 (Qdrant, Ollama)
- Qdrant, Ollama 컨테이너 실행

## 2026-05-13

### 모델 설치
- `bge-m3:latest` — 임베딩 전용 (기존 설치)
- `qwen2.5:7b` — 한국어 특화 LLM
- `llama3.1:8b` — 범용 LLM
- `llama3.2:3b` — 경량 LLM

### mem0 API 서버 구축
- `config.py` — 모델 설정 및 스위칭 지원
- `app.py` — FastAPI 기반 mem0 래퍼
- `Dockerfile` — mem0 컨테이너 이미지
- `requirements.txt` — Python 의존성
- `docker-compose.yml` — mem0 서비스 추가

### 트러블슈팅
| 문제 | 원인 | 해결 |
|------|------|------|
| `EOFError` | `ollama` Python 패키지 누락 | `requirements.txt`에 `ollama` 추가 |
| 벡터 차원 불일치 (1536 vs 1024) | Qdrant 컬렉션이 OpenAI 기본값(1536)으로 생성됨 | `vector_store` 설정에 `embedding_model_dims: 1024` 추가 후 컬렉션 재생성 |
| `get_all` API 오류 | mem0 v2에서 `user_id` 파라미터 방식 변경 | `filters={"user_id": ...}` 방식으로 수정 |

### 기능 검증
- 메모리 추가, 조회, 수정, 삭제, 시맨틱 검색 전부 정상 동작 확인

## 2026-05-14

### Claude Code MCP 연동
- `mcp_server.py` — FastMCP 기반 MCP 서버 작성 (add_memory, search_memory, get_all_memories)
- `.mcp.json` — Claude Code MCP 서버 등록 (timeout: 120000ms)
- `pip3 install mcp httpx` — 호스트에 MCP 패키지 설치

### GPU 성능 이슈 해결
- **문제:** Docker Ollama가 Apple Silicon Metal GPU 미사용 (`size_vram: 0`) → CPU 추론으로 요청당 3분 30초 소요
- **원인:** Docker는 macOS Metal GPU 패스스루 미지원
- **해결:** Ollama를 Docker에서 제거하고 네이티브(`brew install ollama`)로 전환
  - `docker-compose.yml`에서 ollama 서비스 제거
  - `config.py` Ollama URL을 `http://ollama:11434` → `http://host.docker.internal:11434` 변경
  - `docker-compose.yml`에 `extra_hosts: host.docker.internal:host-gateway` 추가
- **결과:** GPU 활성화 후 요청당 13초로 단축

### 트러블슈팅
| 문제 | 원인 | 해결 |
|------|------|------|
| MCP `add_memory` 타임아웃 | httpx 기본 타임아웃 5초 | `mcp_server.py` 모든 httpx 호출에 `timeout=120.0` 추가 |
| 기본 모델 속도 | `qwen2.5:7b`(4.7GB)가 기본값 | 기본 모델을 `llama3.2:3b`(2GB)로 변경 |
