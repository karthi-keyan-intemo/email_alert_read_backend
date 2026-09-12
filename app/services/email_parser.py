def get_error_type(subject: str | None) -> str | None:

    if not subject:
        return None

    subject = subject.strip().lower()

    if subject.startswith("unknown error found"):
        return "UNKNOWN"

    if subject.startswith("response validation error found"):
        return "RESPONSE_VALIDATION"

    return None