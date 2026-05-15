FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir httpx "mcp[cli]"

COPY mcp_server.py .

CMD ["python3", "mcp_server.py"]
