from __future__ import annotations

from difflib import unified_diff


class DiffManager:
    def diff(self, previous: str, current: str) -> str:
        return "\n".join(
            unified_diff(
                previous.splitlines(),
                current.splitlines(),
                fromfile="previous",
                tofile="current",
                lineterm="",
            )
        )


diff_manager = DiffManager()
