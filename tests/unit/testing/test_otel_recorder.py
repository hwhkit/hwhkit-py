"""Tests for hwhkit.testing.otel_recorder."""

from __future__ import annotations

from hwhkit.testing.otel_recorder import OtelRecorder


class TestOtelRecorder:
    def test_records_spans(self) -> None:
        rec = OtelRecorder()
        with rec.span("op-1") as span:
            span.set_attribute("k", "v")
        assert len(rec.spans) == 1
        assert rec.spans[0].name == "op-1"
        assert rec.spans[0].attributes["k"] == "v"

    def test_span_records_exceptions(self) -> None:
        rec = OtelRecorder()
        with rec.span("op") as span:
            span.record_exception(ValueError("oops"))
        assert isinstance(rec.spans[0].exceptions[0], ValueError)

    def test_records_counters(self) -> None:
        rec = OtelRecorder()
        c = rec.counter("requests")
        c.add(1, {"method": "GET"})
        c.add(2, {"method": "POST"})
        assert rec.counter_total("requests") == 3
        assert rec.counter_with("requests", {"method": "GET"}) == 1

    def test_records_histograms(self) -> None:
        rec = OtelRecorder()
        h = rec.histogram("latency")
        h.record(10.0)
        h.record(20.0)
        assert h._rec._histograms["latency"] == [(10.0, {}), (20.0, {})]

    def test_meter_factory_methods(self) -> None:
        rec = OtelRecorder()
        c = rec.create_counter("c", unit="1", description="d")
        h = rec.create_histogram("h", unit="ms", description="d")
        c.add(1)
        h.record(5.0)
        assert rec.counter_total("c") == 1

    def test_records_logs(self) -> None:
        rec = OtelRecorder()
        rec.log_emitter.emit("info", "hello", user="alice")
        assert len(rec.logs) == 1
        assert rec.logs[0].event == "hello"
        assert rec.logs[0].fields["user"] == "alice"

    def test_reset_clears_state(self) -> None:
        rec = OtelRecorder()
        with rec.span("x"):
            pass
        rec.counter("c").add(1)
        rec.log_emitter.emit("info", "e")
        rec.reset()
        assert rec.spans == []
        assert rec.counter_total("c") == 0
        assert rec.logs == []
