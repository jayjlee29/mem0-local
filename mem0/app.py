from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from mem0 import Memory
from config import get_config, MODELS

app = FastAPI(title="mem0 local")

memory_instances: dict[str, Memory] = {}


def get_memory(model: str) -> Memory:
    if model not in memory_instances:
        memory_instances[model] = Memory.from_config(get_config(model))
    return memory_instances[model]


class AddRequest(BaseModel):
    user_id: str
    messages: list[dict]
    model: str = "qwen"


class SearchRequest(BaseModel):
    user_id: str
    query: str
    model: str = "qwen"


class UpdateRequest(BaseModel):
    data: str
    model: str = "qwen"


@app.get("/models")
def list_models():
    return {"models": MODELS}


@app.post("/memories")
def add_memory(req: AddRequest):
    m = get_memory(req.model)
    result = m.add(req.messages, user_id=req.user_id)
    return result


@app.get("/memories/{user_id}")
def get_memories(user_id: str, model: str = "qwen"):
    m = get_memory(model)
    return m.get_all(filters={"user_id": user_id})


@app.patch("/memories/{memory_id}")
def update_memory(memory_id: str, req: UpdateRequest):
    m = get_memory(req.model)
    return m.update(memory_id, req.data)


@app.post("/search")
def search_memory(req: SearchRequest):
    m = get_memory(req.model)
    return m.search(req.query, filters={"user_id": req.user_id})


@app.delete("/memories/{user_id}")
def delete_memories(user_id: str, model: str = "qwen"):
    m = get_memory(model)
    m.delete_all(filters={"user_id": user_id})
    return {"status": "deleted"}


@app.delete("/memory/{memory_id}")
def delete_memory(memory_id: str, model: str = "qwen"):
    m = get_memory(model)
    m.delete(memory_id)
    return {"status": "deleted", "id": memory_id}
