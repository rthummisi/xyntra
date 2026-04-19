from core.telemetry import telemetry_recorder


def test_telemetry_recorder_exports_spans() -> None:
    telemetry_recorder.spans.clear()
    with telemetry_recorder.span("test-span", scope="unit"):
        pass

    exported = telemetry_recorder.export()

    assert exported[0]["name"] == "test-span"
    assert exported[0]["attributes"]["scope"] == "unit"
