# mem0-local

로컬 환경에서 완전 무료로 동작하는 두 가지 기능을 제공한다.

1. **mem0 메모리 시스템** — Claude Code에 장기 메모리 추가 (MCP)
2. **Ollama + Claude CLI 연동** — LiteLLM 프록시를 통해 로컬 LLM으로 Claude Code 구동

---

# Part 1. mem0 메모리 시스템

## 아키텍처

```
Claude Code (MCP)
      │
      ▼
mem0-mcp-server ──►  mem0 API (Docker :8000)
(Docker :8001)             │
                  ┌────────┤
                  ▼        ▼
            Qdrant       mem0 라이브러리
          벡터 DB :6333        │
                               ▼
                        Ollama (Native :11434)
                          Metal GPU
```

> **Ollama는 네이티브로 실행** — Docker 컨테이너는 Apple Silicon Metal GPU에 접근 불가.

## 디렉토리 구조

```
mem0-local/
├── mem0/                  # mem0 API 서버
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app.py
│   └── config.py
├── mem0-mcp-server/       # Claude Code MCP 서버
│   ├── Dockerfile
│   └── mcp_server.py
├── docker-compose.yml
└── .mcp.json              # Claude Code MCP 연결 설정
```

## 구성 서비스

| 서비스 | 실행 방식 | 역할 | 포트 |
|--------|-----------|------|------|
| Qdrant | Docker | 벡터 DB (메모리 저장소) | 6333 |
| Ollama | 네이티브 (brew) | 로컬 LLM 서버 (GPU) | 11434 |
| mem0 | Docker | 메모리 API 서버 (FastAPI) | 8000 |
| mem0-mcp-server | Docker | Claude Code MCP 서버 (SSE) | 8001 |

## 모델

### 임베딩 모델

| 모델 | 용도 | 용량 | 벡터 차원 |
|------|------|------|----------|
| `bge-m3` | 텍스트 → 벡터 변환 (다국어 지원) | 1.2GB | 1024 |

### LLM (메모리 추출용)

| 별칭 | 모델 | 용량 | 속도 | 한국어 | 추천 용도 |
|------|------|------|------|--------|----------|
| `llama3-mini` | `llama3.2:3b` | 2.0GB | ~13초 | 보통 | 빠른 응답 |
| `qwen` ⭐ | `qwen2.5:7b` | 4.7GB | ~25초 | 우수 | **기본값** — 한국어 메모리 |
| `llama3` | `llama3.1:8b` | 4.9GB | ~30초 | 보통 | 영어 기술 문서 |

> 속도는 Apple Silicon M-series 기준 (Ollama 네이티브, Metal GPU 활성화)

## 설치

### 자동 설치 (권장)

```bash
./setup.sh
```

### 수동 설치

```bash
# 1. Ollama 설치 및 모델 다운로드
brew install ollama && brew services start ollama
ollama pull bge-m3
ollama pull llama3.2:3b
ollama pull qwen2.5:7b

# 2. Docker 서비스 실행
docker compose up -d
```

### Claude Code MCP 연동

프로젝트 루트의 `.mcp.json`이 자동으로 MCP 서버를 등록한다.

```json
{
  "mcpServers": {
    "mem0": {
      "type": "sse",
      "url": "http://localhost:8001/sse"
    }
  }
}
```

Claude Code 재시작 후 `/mcp`로 연결 확인.

## MCP 툴

| 툴 | 설명 |
|----|------|
| `add_memory` | 메모리 저장 |
| `search_memory` | 시맨틱 검색 |
| `get_all_memories` | 전체 메모리 조회 |
| `delete_memory` | 단건 메모리 삭제 |

## REST API

### 메모리 추가
```bash
curl -X POST http://localhost:8000/memories \
  -H "Content-Type: application/json" \
  -d '{"user_id": "jay", "messages": [{"role": "user", "content": "나는 서비스 엔지니어야"}], "model": "qwen"}'
```

### 메모리 조회
```bash
curl "http://localhost:8000/memories/{user_id}"
```

### 시맨틱 검색
```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"user_id": "jay", "query": "직업", "model": "qwen"}'
```

### 메모리 수정
```bash
curl -X PATCH http://localhost:8000/memories/{memory_id} \
  -H "Content-Type: application/json" \
  -d '{"data": "수정할 내용"}'
```

### 메모리 삭제 (단건)
```bash
curl -X DELETE "http://localhost:8000/memory/{memory_id}"
```

### 메모리 삭제 (전체)
```bash
curl -X DELETE "http://localhost:8000/memories/{user_id}"
```

### 모델 스위칭

| 값 | 모델 |
|----|------|
| `llama3-mini` | llama3.2:3b |
| `qwen` | qwen2.5:7b (기본값) |
| `llama3` | llama3.1:8b |

API 문서: http://localhost:8000/docs

---

# Part 2. Ollama + Claude CLI 연동

LiteLLM 프록시를 통해 로컬 Ollama 모델을 Claude Code의 기반 LLM으로 사용한다.

## 아키텍처

```
Claude Code (/model ollama/...)
      │
      ▼
LiteLLM Proxy (Docker :4000)
      │
      ▼
Ollama (Native :11434)
  Metal GPU
```

## 사용법

```bash
ANTHROPIC_BASE_URL=http://localhost:4000 claude
```

실행 후 반드시 모델을 Ollama 모델로 전환:

```
/model ollama/qwen3-14b     # 권장
/model ollama/qwen14b
/model ollama/qwen
/model ollama/llama3.1
/model ollama/qwen-coder
```

## 사용 가능한 모델

| 별칭 | 모델 | 크기 | 추천 용도 |
|------|------|------|----------|
| `ollama/qwen3-14b` ⭐ | `qwen3:14b` | 9.3GB | **권장** — 툴 콜 성능 우수 |
| `ollama/qwen14b` | `qwen2.5:14b` | 9.0GB | 고품질 대화 |
| `ollama/qwen` | `qwen2.5:7b` | 4.7GB | 기본 대화 |
| `ollama/qwen-coder` | `qwen2.5-coder:7b` | 4.7GB | 코딩 특화 |
| `ollama/llama3.1` | `llama3.1:8b` | 4.9GB | 영어 대화 |
| `ollama/llama3.2` | `llama3.2:3b` | 2.0GB | 경량, 빠른 응답 |

> **주의:** Ollama 모델은 Claude Code의 복잡한 시스템 프롬프트와 툴 콜을 완전히 지원하지 않아 응답 품질이 Claude 모델보다 낮을 수 있다. 14b 이상 모델 사용을 권장한다.
