from __future__ import annotations

import asyncio
from collections import defaultdict

from agents.types import IPCMessage


class IPCBus:
    """Async inter-agent message bus using per-agent asyncio queues."""

    def __init__(self) -> None:
        self._queues: dict[str, asyncio.Queue[IPCMessage]] = defaultdict(asyncio.Queue)
        self._history: list[IPCMessage] = []

    def send(self, message: IPCMessage) -> None:
        queue = self._queues[message.to_agent]
        queue.put_nowait(message)
        self._history.append(message)

    async def receive(self, agent_id: str, timeout: float = 30.0) -> IPCMessage | None:
        queue = self._queues[agent_id]
        try:
            return await asyncio.wait_for(queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None

    def drain(self, agent_id: str) -> list[IPCMessage]:
        queue = self._queues[agent_id]
        messages: list[IPCMessage] = []
        while not queue.empty():
            messages.append(queue.get_nowait())
        return messages

    def history(self, limit: int = 100) -> list[IPCMessage]:
        return self._history[-limit:]

    def clear_agent(self, agent_id: str) -> None:
        self._queues.pop(agent_id, None)


ipc_bus = IPCBus()
