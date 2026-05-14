import httpx
from mcp.server.fastmcp import FastMCP

MEM0_URL = "http://localhost:8000"
DEFAULT_USER = "claude"
DEFAULT_MODEL = "qwen"
TIMEOUT = 120.0

mcp = FastMCP("mem0")


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


if __name__ == "__main__":
    mcp.run()
