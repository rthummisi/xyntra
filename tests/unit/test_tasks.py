from tasks.planner import task_planner
from tasks.state_machine import InvalidTaskTransitionError, task_state_machine
from tasks.task_graph import task_graph


def test_task_planner_produces_primary_task() -> None:
    plan = task_planner.plan("implement routing")
    assert plan.tasks[0].name == "primary"
    assert plan.tasks[0].input_payload["objective"] == "implement routing"


def test_task_graph_resolves_dependencies() -> None:
    plan = task_planner.plan("bootstrap")
    ordered = task_graph.resolve(plan)
    assert ordered[0].name == "primary"


def test_task_state_machine_rejects_invalid_transition() -> None:
    try:
        task_state_machine.transition("pending", "completed")
    except InvalidTaskTransitionError as exc:
        assert "Invalid transition" in str(exc)
    else:
        raise AssertionError("Expected invalid transition failure")
