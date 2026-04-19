from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from dataclasses import dataclass, field
from time import perf_counter
from typing import Any


@dataclass
class SpanRecord:
    name: str
    duration_ms: float = 0.0
    attributes: dict[str, Any] = field(default_factory=dict)


class TelemetryRecorder:
    def __init__(self) -> None:
        self.spans: list[SpanRecord] = []
        self._otel_tracer = self._build_tracer()

    @contextmanager
    def span(self, name: str, **attributes: Any):
        start = perf_counter()
        record = SpanRecord(name=name, attributes=attributes)
        if self._otel_tracer is not None:
            with self._otel_tracer.start_as_current_span(name) as current_span:
                for key, value in attributes.items():
                    current_span.set_attribute(key, value)
                try:
                    yield record
                finally:
                    record.duration_ms = round((perf_counter() - start) * 1000, 2)
                    current_span.set_attribute("xyntra.duration_ms", record.duration_ms)
                    self.spans.append(record)
            return
        try:
            yield record
        finally:
            record.duration_ms = round((perf_counter() - start) * 1000, 2)
            self.spans.append(record)

    def export(self) -> list[dict[str, Any]]:
        return [
            {
                "name": span.name,
                "duration_ms": span.duration_ms,
                "attributes": span.attributes,
            }
            for span in self.spans
        ]

    @staticmethod
    def _build_tracer():
        if os.environ.get("PYTEST_CURRENT_TEST") or any(
            "pytest" in argument for argument in sys.argv
        ):
            return None
        try:
            from opentelemetry import trace
            from opentelemetry.sdk.resources import Resource
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import (
                BatchSpanProcessor,
                ConsoleSpanExporter,
            )
        except ImportError:
            return None

        provider = trace.get_tracer_provider()
        if provider.__class__.__name__ == "ProxyTracerProvider":
            tracer_provider = TracerProvider(
                resource=Resource.create({"service.name": "xyntra"})
            )
            tracer_provider.add_span_processor(
                BatchSpanProcessor(ConsoleSpanExporter())
            )
            trace.set_tracer_provider(tracer_provider)

        return trace.get_tracer("xyntra.telemetry")


telemetry_recorder = TelemetryRecorder()
