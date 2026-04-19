from models import Base


def test_metadata_contains_phase2_tables() -> None:
    expected_tables = {
        "approvals",
        "artifacts",
        "dead_letter_queue_entries",
        "decisions",
        "memory_summaries",
        "messages",
        "policy_rules",
        "project_states",
        "projects",
        "prompt_templates",
        "provider_calls",
        "retrieved_contexts",
        "semantic_cache_entries",
        "sessions",
        "spend_records",
        "task_runs",
        "tasks",
        "tool_definitions",
        "users",
        "webhook_events",
        "webhook_subscriptions",
    }

    assert expected_tables.issubset(Base.metadata.tables.keys())
