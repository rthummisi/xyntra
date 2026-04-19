from __future__ import annotations

from collections import defaultdict, deque

from tasks.planner import PlannedTask, TaskPlan


class TaskGraph:
    def resolve(self, plan: TaskPlan) -> list[PlannedTask]:
        by_name = {task.name: task for task in plan.tasks}
        indegree = {task.name: 0 for task in plan.tasks}
        edges: dict[str, list[str]] = defaultdict(list)

        for task in plan.tasks:
            for dependency in task.dependencies:
                if dependency not in by_name:
                    raise ValueError(f"Unknown dependency: {dependency}")
                edges[dependency].append(task.name)
                indegree[task.name] += 1

        queue = deque(
            [by_name[name] for name, degree in indegree.items() if degree == 0]
        )
        ordered: list[PlannedTask] = []
        while queue:
            task = queue.popleft()
            ordered.append(task)
            for dependent in edges[task.name]:
                indegree[dependent] -= 1
                if indegree[dependent] == 0:
                    queue.append(by_name[dependent])

        if len(ordered) != len(plan.tasks):
            raise ValueError("Task graph contains a cycle.")
        return ordered


task_graph = TaskGraph()
