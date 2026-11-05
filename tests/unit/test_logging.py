from finance.shared.logging import redact


def test_sensitive_fields_are_recursively_redacted() -> None:
    assert redact({"text": "350k taxi", "nested": {"note": "private"}, "result": "ok"}) == {
        "text": "[REDACTED]",
        "nested": {"note": "[REDACTED]"},
        "result": "ok",
    }
