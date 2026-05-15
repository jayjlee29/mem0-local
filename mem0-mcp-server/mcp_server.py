import httpx
from mcp.server.fastmcp import FastMCP

import os

MEM0_URL = os.environ.get("MEM0_URL", "http://localhost:8000")
DEFAULT_USER = "claude"
DEFAULT_MODEL = "qwen"
TIMEOUT = 120.0

port = int(os.environ.get("MCP_PORT", "8001"))
mcp = FastMCP("mem0", port=port, host="0.0.0.0")


@mcp.tool()
def add_memory(content: str, user_id: str = DEFAULT_USER, model: str = DEFAULT_MODEL) -> dict:
    """mem0에 새로운 메모리를 저장합니다."""
    response = httpx.post(f"{MEM0_URL}/memories", json={
        "user_id": user_id,
        "messages": [{"role": "user", "content": content}],
        "model": model,
    }, timeout=TIMEOUT)
    return response.json()


@mcp.tool()
def search_memory(query: str, user_id: str = DEFAULT_USER, model: str = DEFAULT_MODEL) -> dict:
    """쿼리와 관련된 메모리를 시맨틱 검색합니다."""
    response = httpx.post(f"{MEM0_URL}/search", json={
        "user_id": user_id,
        "query": query,
        "model": model,
    }, timeout=TIMEOUT)
    return response.json()


@mcp.tool()
def get_all_memories(user_id: str = DEFAULT_USER, model: str = DEFAULT_MODEL) -> dict:
    """저장된 모든 메모리를 가져옵니다."""
    response = httpx.get(f"{MEM0_URL}/memories/{user_id}", params={"model": model}, timeout=TIMEOUT)
    return response.json()


@mcp.tool()
def delete_memory(memory_id: str, user_id: str = DEFAULT_USER) -> dict:
    """메모리를 삭제합니다.

    주의: 이 툴을 호출하기 전에 반드시 다음 절차를 따르세요.
    1. search_memory 또는 get_all_memories로 삭제 대상을 찾는다.
    2. 삭제할 메모리의 내용(memory 필드)을 사용자에게 보여준다.
    3. 사용자에게 명시적으로 삭제 여부를 확인한다.
    4. 사용자가 확인한 경우에만 이 툴을 호출한다.
    """
    response = httpx.delete(f"{MEM0_URL}/memory/{memory_id}", timeout=TIMEOUT)
    return response.json()


if __name__ == "__main__":
    transport = os.environ.get("MCP_TRANSPORT", "stdio")
    mcp.run(transport=transport)
