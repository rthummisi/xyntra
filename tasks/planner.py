from __future__ import annotations

from pydantic import BaseModel, Field


class PlannedTask(BaseModel):
    name: str
    task_type: str
    description: str | None = None
    dependencies: list[str] = Field(default_factory=list)
    input_payload: dict = Field(default_factory=dict)


class TaskPlan(BaseModel):
    tasks: list[PlannedTask] = Field(default_factory=list)


class TaskPlanner:
    def plan(self, objective: str) -> TaskPlan:
        return TaskPlan(
            tasks=[
                PlannedTask(
                    name="primary",
                    task_type="execution",
                    description=objective,
                    input_payload={"objective": objective},
                )
            ]
        )


task_planner = TaskPlanner()
