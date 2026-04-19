from __future__ import annotations


class InvalidTaskTransitionError(ValueError):
    pass


TASK_TRANSITIONS: dict[str, set[str]] = {
    "pending": {"queued", "cancelled"},
    "queued": {"running", "cancelled"},
    "running": {"completed", "failed", "cancelled"},
    "failed": {"queued", "cancelled"},
    "completed": set(),
    "cancelled": set(),
}


class TaskStateMachine:
    def transition(self, current: str, target: str) -> str:
        allowed = TASK_TRANSITIONS.get(current, set())
        if target not in allowed:
            raise InvalidTaskTransitionError(
                f"Invalid transition from {current} to {target}"
            )
        return target


task_state_machine = TaskStateMachine()
