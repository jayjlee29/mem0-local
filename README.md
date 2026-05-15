# mem0-local

로컬 환경에서 완전 무료로 동작하는 AI 메모리 시스템

## 아키텍처

```
Claude Code (MCP)          Claude Code (/model)
      │                           │
      ▼                           ▼
mem0-mcp-server ──►  mem0 API   LiteLLM Proxy (Docker :4000)
(Docker :8001)      (Docker          │
                     :8000)          ▼
                       │       Ollama (Native :11434)
          ┌────────────┤         Metal GPU
          ▼            ▼
    Qdrant (Docker)  mem0 라이브러리
     벡터 DB :6333
```

> **Ollama는 네이티브로 실행** — Docker 컨테이너는 Apple Silicon Metal GPU에 접근 불가. GPU 사용을 위해 Ollama를 호스트에서 직접 실행.

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

## 구성

| 서비스 | 실행 방식 | 역할 | 포트 |
|--------|-----------|------|------|
| Qdrant | Docker | 벡터 DB (메모리 저장소) | 6333 |
| Ollama | 네이티브 (brew) | 로컬 LLM 서버 (GPU) | 11434 |
| mem0 | Docker | 메모리 API 서버 (FastAPI) | 8000 |
| mem0-mcp-server | Docker | Claude Code MCP 서버 (SSE) | 8001 |
| LiteLLM | Docker | Ollama → Claude Code 프록시 | 4000 |

## 모델

### 임베딩 모델

| 모델 | 용도 | 용량 | 벡터 차원 |
|------|------|------|----------|
| `bge-m3` | 텍스트 → 벡터 변환 (다국어 지원) | 1.2GB | 1024 |

bge-m3는 한국어·영어 혼합 텍스트에서 높은 품질의 임베딩을 생성한다. Qdrant 컬렉션은 반드시 `embedding_model_dims: 1024`로 설정해야 한다.

### LLM (메모리 추출용)

| 별칭 | 모델 | 용량 | 속도 | 한국어 | 추천 용도 |
|------|------|------|------|--------|----------|
| `llama3-mini` | `llama3.2:3b` | 2.0GB | ~13초 | 보통 | 빠른 응답이 필요한 경우 |
| `qwen` ⭐ | `qwen2.5:7b` | 4.7GB | ~25초 | 우수 | **기본값** — 한국어 메모리 저장/검색 |
| `llama3` | `llama3.1:8b` | 4.9GB | ~30초 | 보통 | 영어 기술 문서, 복잡한 컨텍스트 추론 |

> **속도는 Apple Silicon M-series 기준** (Ollama 네이티브, Metal GPU 활성화)
>
> **기본값은 `qwen`** — 한국어 위주 환경에서 추출 정확도 우선.
> 속도가 중요한 경우에만 `llama3-mini`로 명시적으로 지정한다.

### Claude Code 연동용 LLM (LiteLLM 프록시)

| 별칭 | 모델 | 크기 | 추천 용도 |
|------|------|------|----------|
| `ollama/qwen` | `qwen2.5:7b` | 4.7GB | 기본 대화 |
| `ollama/qwen14b` | `qwen2.5:14b` | 9.0GB | 고품질 대화 |
| `ollama/qwen3-14b` | `qwen3:14b` | 9.3GB | 최신 모델, 툴 콜 성능 향상 ⭐ |
| `ollama/qwen-coder` | `qwen2.5-coder:7b` | 4.7GB | 코딩 특화 |
| `ollama/llama3.1` | `llama3.1:8b` | 4.9GB | 영어 대화 |
| `ollama/llama3.2` | `llama3.2:3b` | 2.0GB | 경량, 빠른 응답 |

### 모델 선택 가이드

```
빠른 메모리 저장/검색    → llama3-mini (기본값)
한국어 인시던트 기록     → qwen
영어 기술 문서 분석      → llama3
Claude Code 연동 (권장)  → qwen3-14b
```

## 설치

### 자동 설치 (권장)

```bash
./setup.sh
```

Ollama 설치, 모델 다운로드, Docker 서비스 실행까지 한 번에 진행한다.

### 수동 설치

#### 1. Ollama 네이티브 설치 및 모델 다운로드

```bash
brew install ollama
brew services start ollama

ollama pull bge-m3
ollama pull llama3.2:3b
ollama pull qwen2.5:7b
ollama pull llama3.1:8b
```

#### 2. Docker 서비스 실행

```bash
docker compose up -d
```

#### 3. Claude Code MCP 연동

프로젝트 루트의 `.mcp.json`이 자동으로 MCP 서버를 등록합니다.

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

---

### Claude Code에서 Ollama 모델 직접 사용 (선택)

LiteLLM 프록시가 Docker로 함께 실행되므로 별도 설치 없이 바로 사용 가능하다.

```bash
ANTHROPIC_BASE_URL=http://localhost:4000 claude
```

세션 중 모델 전환:

```
/model ollama/qwen3-14b     # 권장
/model ollama/qwen14b
/model ollama/qwen
/model ollama/llama3.1
/model ollama/qwen-coder
```

## Claude Code MCP 사용법

Claude Code 대화 중 자동으로 mem0 툴을 사용할 수 있습니다.

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
  -d '{"user_id": "jay", "messages": [{"role": "user", "content": "나는 서비스 엔지니어야"}], "model": "llama3-mini"}'
```

### 메모리 조회
```bash
curl "http://localhost:8000/memories/{user_id}?model=llama3-mini"
```

### 메모리 수정
```bash
curl -X PATCH http://localhost:8000/memories/{memory_id} \
  -H "Content-Type: application/json" \
  -d '{"data": "수정할 내용", "model": "llama3-mini"}'
```

### 메모리 삭제 (전체)
```bash
curl -X DELETE "http://localhost:8000/memories/{user_id}"
```

### 메모리 삭제 (단건)
```bash
curl -X DELETE "http://localhost:8000/memory/{memory_id}"
```

### 시맨틱 검색
```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"user_id": "jay", "query": "직업", "model": "llama3-mini"}'
```

### 모델 스위칭

모든 API에서 `model` 파라미터로 LLM을 변경할 수 있습니다.

| 값 | 모델 |
|----|------|
| `llama3-mini` | llama3.2:3b (기본값) |
| `qwen` | qwen2.5:7b |
| `llama3` | llama3.1:8b |

## 활용 시나리오

### 1. 인시던트 기록 및 재발 방지

```bash
# 인시던트 발생 시 기록 (한국어 정확도가 필요하면 qwen 사용)
curl -X POST http://localhost:8000/memories \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "jay",
    "messages": [{"role": "user", "content":
      "Jay가 담당하는 결제서비스에서 오전 9시 DB 커넥션 풀 고갈이 발생했다. max_connections를 100에서 200으로 늘려서 해결했다. 2026-05-14"
    }],
    "model": "qwen"
  }'

# 다음번 유사 문제 분석 시 검색
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"user_id": "jay", "query": "결제서비스 타임아웃"}'
```

### 2. 설정 변경 이력 관리

```bash
curl -X POST http://localhost:8000/memories \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "jay",
    "messages": [{"role": "user", "content":
      "Jay는 알림서비스의 Kafka consumer timeout을 30초에서 60초로 변경했다. 이유는 대용량 배치 메시지 처리 시 재처리가 발생했기 때문이다."
    }],
    "model": "llama3-mini"
  }'
```

### 3. Claude Code에서 자동 활용 (MCP)

Claude Code 대화 중 Claude가 자동으로 mem0 툴을 호출한다:

```
사용자: "결제서비스 DB 연결이 자꾸 끊겨요"
Claude: [search_memory("결제서비스 DB 연결")] → 과거 인시던트 기록 참조
        → "2026-05-14에 같은 문제가 있었습니다. max_connections 설정을 확인해보세요."

사용자: "배포 완료됐어요, Kafka timeout 60초로 변경했고 별 문제 없었어요"
Claude: [add_memory("Jay는 알림서비스 Kafka timeout을 60초로 변경 완료. 정상 배포. 2026-05-14")]
```

## API 문서

서버 실행 후 http://localhost:8000/docs 에서 Swagger UI 확인 가능
