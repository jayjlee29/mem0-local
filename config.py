MODELS = {
    "qwen": "qwen2.5:7b",
    "llama3": "llama3.1:8b",
    "llama3-mini": "llama3.2:3b",
}

DEFAULT_MODEL = "qwen"


def get_config(model: str = DEFAULT_MODEL) -> dict:
    model_name = MODELS.get(model, model)
    return {
        "llm": {
            "provider": "ollama",
            "config": {
                "model": model_name,
                "ollama_base_url": "http://host.docker.internal:11434",
            },
        },
        "embedder": {
            "provider": "ollama",
            "config": {
                "model": "bge-m3:latest",
                "ollama_base_url": "http://host.docker.internal:11434",
            },
        },
        "vector_store": {
            "provider": "qdrant",
            "config": {
                "host": "qdrant",
                "port": 6333,
                "embedding_model_dims": 1024,
            },
        },
    }
