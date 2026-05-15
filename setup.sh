#!/usr/bin/env bash
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()    { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; exit 1; }
step()    { echo -e "\n${GREEN}==>${NC} $*"; }

MODELS_REQUIRED=(bge-m3 llama3.2:3b)
MODELS_OPTIONAL=(qwen2.5:7b llama3.1:8b)

# ── 1. 사전 요건 확인 ────────────────────────────────────────────────────────

step "사전 요건 확인"

command -v brew  >/dev/null 2>&1 || error "Homebrew가 설치되어 있지 않습니다. https://brew.sh 에서 설치 후 재실행하세요."
command -v docker >/dev/null 2>&1 || error "Docker가 설치되어 있지 않습니다. Docker Desktop을 설치 후 재실행하세요."
command -v python3 >/dev/null 2>&1 || error "python3가 설치되어 있지 않습니다."

docker info >/dev/null 2>&1 || error "Docker 데몬이 실행중이지 않습니다. Docker Desktop을 실행 후 재실행하세요."

info "사전 요건 확인 완료"

# ── 2. Ollama 설치 및 실행 ───────────────────────────────────────────────────

step "Ollama 설치 확인"

if command -v ollama >/dev/null 2>&1; then
    info "Ollama 이미 설치됨: $(ollama --version 2>/dev/null || echo '버전 확인 불가')"
else
    info "Ollama 설치 중..."
    brew install ollama
fi

if brew services list | grep ollama | grep -q started; then
    info "Ollama 서비스 실행 중"
else
    info "Ollama 서비스 시작 중..."
    brew services start ollama
    sleep 3
fi

# Ollama 응답 대기 (최대 30초)
info "Ollama 응답 대기 중..."
for i in $(seq 1 30); do
    if curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then
        info "Ollama 준비 완료"
        break
    fi
    if [ "$i" -eq 30 ]; then
        error "Ollama가 30초 내에 응답하지 않습니다. 'brew services restart ollama' 후 재시도하세요."
    fi
    sleep 1
done

# ── 3. 모델 다운로드 ─────────────────────────────────────────────────────────

step "필수 모델 다운로드"
for model in "${MODELS_REQUIRED[@]}"; do
    if ollama list 2>/dev/null | grep -q "^${model}"; then
        info "$model — 이미 설치됨"
    else
        info "$model 다운로드 중..."
        ollama pull "$model"
    fi
done

step "선택 모델 다운로드"
for model in "${MODELS_OPTIONAL[@]}"; do
    if ollama list 2>/dev/null | grep -q "^${model%:*}"; then
        info "$model — 이미 설치됨"
    else
        read -r -p "  $model 을 다운로드하시겠습니까? [y/N] " ans
        if [[ "${ans,,}" == "y" ]]; then
            ollama pull "$model"
        else
            warn "$model 건너뜀 (나중에 'ollama pull $model'로 설치 가능)"
        fi
    fi
done

# ── 4. Docker 서비스 시작 ────────────────────────────────────────────────────

step "Docker 서비스 시작 (Qdrant + mem0 + mem0-mcp-server + LiteLLM)"
docker compose up -d --build

# mem0 헬스체크 대기 (최대 60초)
info "mem0 API 응답 대기 중..."
for i in $(seq 1 60); do
    if curl -sf http://localhost:8000/models >/dev/null 2>&1; then
        info "mem0 API 준비 완료"
        break
    fi
    if [ "$i" -eq 60 ]; then
        warn "mem0가 60초 내에 응답하지 않습니다. 'docker compose logs mem0'로 확인하세요."
        break
    fi
    sleep 1
done

# ── 5. 연결 확인 ─────────────────────────────────────────────────────────────

step "서비스 연결 확인"

check_service() {
    local name=$1 url=$2
    if curl -sf "$url" >/dev/null 2>&1; then
        info "$name ✓ ($url)"
    else
        warn "$name 응답 없음 ($url)"
    fi
}

check_service "Ollama"          "http://localhost:11434/api/tags"
check_service "Qdrant"          "http://localhost:6333/healthz"
check_service "mem0 API"        "http://localhost:8000/models"
check_service "mem0 MCP Server" "http://localhost:8001/sse"
check_service "LiteLLM"         "http://localhost:4000/health"

# ── 완료 ─────────────────────────────────────────────────────────────────────

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}  설치 완료!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "  mem0 API        : http://localhost:8000"
echo "  API 문서        : http://localhost:8000/docs"
echo "  mem0 MCP Server : http://localhost:8001/sse"
echo "  Qdrant UI       : http://localhost:6333/dashboard"
echo "  LiteLLM         : http://localhost:4000"
echo ""
echo "  Claude Code 재시작 후 /mcp 명령으로 연결을 확인하세요."
echo ""
echo "  Ollama 모델 사용:"
echo "    ANTHROPIC_BASE_URL=http://localhost:4000 claude"
echo ""
