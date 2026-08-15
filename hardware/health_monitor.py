from __future__ import annotations

import asyncio
from datetime import datetime

from hardware.inventory import SystemInventory, snapshot


class HardwareHealthMonitor:
    """Periodic hardware sampling — kept in memory, no DB dependency."""

    def __init__(self, interval_seconds: float = 5.0) -> None:
        self._interval = interval_seconds
        self._current: SystemInventory | None = None
        self._history: list[SystemInventory] = []
        self._max_history = 120  # 10 minutes at 5s interval
        self._task: asyncio.Task | None = None

    @property
    def current(self) -> SystemInventory | None:
        return self._current

    def sample_now(self) -> SystemInventory:
        inv = snapshot()
        self._current = inv
        self._history.append(inv)
        if len(self._history) > self._max_history:
            self._history.pop(0)
        return inv

    def recent_history(self, n: int = 20) -> list[SystemInventory]:
        return self._history[-n:]

    async def _loop(self) -> None:
        while True:
            try:
                self.sample_now()
            except Exception:
                pass
            await asyncio.sleep(self._interval)

    def start(self) -> None:
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._loop())

    def stop(self) -> None:
        if self._task and not self._task.done():
            self._task.cancel()


hw_monitor = HardwareHealthMonitor(interval_seconds=5.0)
