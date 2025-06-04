"""Core classes for the NAN multi-agent memory system using Redis storage and
Ollama for text generation."""

from __future__ import annotations

import json
import uuid
from typing import Iterable, List

import redis
import requests


REDIS_HOST = "localhost"
REDIS_PORT = 6379

_REDIS = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


class MemoryPool:
    """Manage detached memory chunks for agents using Redis."""

    def __init__(self, redis_client: redis.Redis = _REDIS) -> None:
        self.redis = redis_client

    def _key(self, memory_id: str) -> str:
        return f"pool:{memory_id}"

    def add_memory(self, memory: Iterable[str]) -> str:
        """Add a memory list to the pool and return a unique id."""
        memory_id = str(uuid.uuid4())
        self.redis.set(self._key(memory_id), json.dumps(list(memory)))
        self.redis.sadd("pool_ids", memory_id)
        return memory_id

    def get_memory(self, memory_id: str) -> List[str] | None:
        data = self.redis.get(self._key(memory_id))
        return json.loads(data) if data else None

    def remove_memory(self, memory_id: str) -> List[str] | None:
        memory = self.get_memory(memory_id)
        if memory is not None:
            self.redis.delete(self._key(memory_id))
            self.redis.srem("pool_ids", memory_id)
        return memory

    def list_memory_ids(self) -> List[str]:
        return list(self.redis.smembers("pool_ids"))


class Agent:
    """Simple agent holding its own memory in Redis."""

    def __init__(self, agent_id: str, redis_client: redis.Redis = _REDIS) -> None:
        self.id = agent_id
        self.redis = redis_client

    def _key(self) -> str:
        return f"agent:{self.id}:mem"

    def add_memory(self, item: str) -> None:
        self.redis.rpush(self._key(), item)

    def query_memory(self) -> List[str]:
        return self.redis.lrange(self._key(), 0, -1)

    def clear_memory(self) -> None:
        self.redis.delete(self._key())

    def detach_memory(self, pool: MemoryPool) -> str:
        memory = self.query_memory()
        memory_id = pool.add_memory(memory)
        self.clear_memory()
        return memory_id

    def attach_memory(self, pool: MemoryPool, memory_id: str) -> bool:
        memory = pool.remove_memory(memory_id)
        if memory is not None:
            self.clear_memory()
            if memory:
                self.redis.rpush(self._key(), *memory)
            return True
        return False

    def save_memory(self, filepath: str) -> None:
        with open(filepath, "w", encoding="utf-8") as f:
            for item in self.query_memory():
                f.write(f"{item}\n")

    def load_memory(self, filepath: str) -> None:
        self.clear_memory()
        with open(filepath, "r", encoding="utf-8") as f:
            items = [line.strip() for line in f]
        if items:
            self.redis.rpush(self._key(), *items)


class OllamaClient:
    """Minimal client for interacting with an Ollama server."""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama2") -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    def generate(self, prompt: str) -> str:
        resp = requests.post(
            f"{self.base_url}/api/generate",
            json={"model": self.model, "prompt": prompt, "stream": False},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("response", "")

