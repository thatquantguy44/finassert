"""Human-readable policy actions, separate from actual validation outcomes."""


def failure_action(severity: str) -> str:
    """Describe a configured failure's effect without implying it occurred."""
    return {
        "error": "Block validation",
        "warning": "Show warning",
        "info": "Show information",
    }.get(severity, severity)
