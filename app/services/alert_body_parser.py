import re
from datetime import datetime
from uuid import UUID


REQUEST_ID_PATTERN = re.compile(
    r"Request ID\s*:\s*([0-9a-fA-F-]{36})",
    re.IGNORECASE,
)


FIELD_PATTERNS = {
    "environment": re.compile(
        r"Environment\s*:\s*(.*?)(?=\n|$)",
        re.IGNORECASE,
    ),
    "source_name": re.compile(
        r"Source Name\s*:\s*(.*?)(?=\n|$)",
        re.IGNORECASE,
    ),
    "azure_task": re.compile(
        r"Azure Task\s*:\s*(.*?)(?=\n|$)",
        re.IGNORECASE,
    ),
    "timestamp": re.compile(
        r"Timestamp\s*:\s*(.*?)(?=\n|$)",
        re.IGNORECASE,
    ),
}


ERROR_MESSAGE_PATTERN = re.compile(
    r"Error Message\s*:\s*(.*?)"
    r"(?=\n\s*Reference ID\s*:|\n\s*Timestamp\s*:|$)",
    re.IGNORECASE | re.DOTALL,
)


def parse_alert_body(body: str) -> dict:

    fields = {}

    # ---------------------------------------------------------
    # Single-line fields
    # ---------------------------------------------------------
    for field_name, pattern in FIELD_PATTERNS.items():
        match = pattern.search(body)

        if match:
            fields[field_name] = match.group(1).strip()

    # ---------------------------------------------------------
    # Multi-line error message
    # ---------------------------------------------------------
    error_match = ERROR_MESSAGE_PATTERN.search(body)

    if error_match:
        error_message = error_match.group(1).strip()

        # Normalize excessive blank lines
        error_message = re.sub(
            r"\n\s*\n+",
            "\n",
            error_message,
        )

        fields["error_message"] = error_message
    else:
        fields["error_message"] = None

    # ---------------------------------------------------------
    # Request IDs
    # ---------------------------------------------------------
    request_ids = []

    for match in REQUEST_ID_PATTERN.finditer(body):
        request_id_value = match.group(1).strip()

        try:
            request_id = UUID(request_id_value)
            request_ids.append(request_id)
        except ValueError:
            continue

    # Remove duplicate request IDs
    request_ids = list(dict.fromkeys(request_ids))

    # ---------------------------------------------------------
    # Timestamp
    # ---------------------------------------------------------
    alert_timestamp = None

    timestamp = fields.get("timestamp")

    if timestamp:
        try:
            alert_timestamp = datetime.strptime(
                timestamp,
                "%d %b %Y, %I:%M:%S %p",
            )
        except ValueError:
            pass

    return {
        "environment": fields.get("environment"),
        "source_name": fields.get("source_name"),
        "error_message": fields.get("error_message"),
        "alert_timestamp": alert_timestamp,
        "azure_task": fields.get("azure_task"),
        "request_ids": request_ids,
    }