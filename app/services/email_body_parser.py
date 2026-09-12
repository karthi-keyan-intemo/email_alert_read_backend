from email.message import Message

from bs4 import BeautifulSoup


def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for element in soup(["script", "style"]):
        element.decompose()

    lines = []

    for line in soup.get_text(separator="\n").splitlines():
        line = line.strip()

        if line:
            lines.append(line)

    return "\n".join(lines)


def get_body(message: Message) -> dict[str, str]:
        """
        Extract both plain-text and HTML content from an email.

        Returns:
            {
                "body": plain_text_content,
                "html_body": html_content,
            }
        """

        plain_parts: list[str] = []
        html_parts: list[str] = []

        def decode_payload(part: Message) -> str:
            payload = part.get_payload(
                decode=True
            )

            if not payload:
                return ""

            charset = (
                part.get_content_charset()
                or "utf-8"
            )

            try:
                return payload.decode(
                    charset,
                    errors="replace",
                )
            except (
                LookupError,
                UnicodeDecodeError,
            ):
                return payload.decode(
                    "utf-8",
                    errors="replace",
                )

        # ==================================================
        # Multipart email
        # ==================================================

        if message.is_multipart():

            for part in message.walk():

                content_type = (
                    part.get_content_type()
                )

                content_disposition = str(
                    part.get(
                        "Content-Disposition",
                        "",
                    )
                ).lower()

                # Ignore attachments
                if "attachment" in content_disposition:
                    continue

                # ------------------------------
                # Plain text
                # ------------------------------

                if content_type == "text/plain":

                    content = decode_payload(part)

                    if content:
                        plain_parts.append(content)

                # ------------------------------
                # HTML
                # ------------------------------

                elif content_type == "text/html":

                    content = decode_payload(part)

                    if content:
                        html_parts.append(content)

        # ==================================================
        # Non-multipart email
        # ==================================================

        else:

            content_type = (
                message.get_content_type()
            )

            content = decode_payload(message)

            if content_type == "text/html":

                if content:
                    html_parts.append(content)

            elif content:

                plain_parts.append(content)

        # ==================================================
        # Final values
        # ==================================================
        body = "\n\n".join(
            part.strip()
            for part in plain_parts
            if part and part.strip()
        )

        html_body = "\n\n".join(
            part
            for part in html_parts
            if part
        )

        # If there is no plain text, use HTML converted to text
        if not body and html_body:
            body = html_to_text(html_body)

        return {
            "body": body,
            "html_body": html_body,
        }
    


def extract_email_body(message: Message) -> str:

    plain_text = None
    html_text = None

    if message.is_multipart():

        for part in message.walk():

            if part.is_multipart():
                continue

            disposition = part.get_content_disposition()

            if disposition == "attachment":
                continue

            content_type = part.get_content_type()

            try:
                content = part.get_content()
            except Exception:
                continue

            if not content:
                continue

            if (
                content_type == "text/plain"
                and content.strip()
            ):
                plain_text = content

            elif (
                content_type == "text/html"
                and content.strip()
            ):
                html_text = content

    else:

        content_type = message.get_content_type()

        try:
            content = message.get_content()
        except Exception:
            return ""

        if content_type == "text/plain":
            plain_text = content

        elif content_type == "text/html":
            html_text = content

    if plain_text:
        return plain_text.strip()

    if html_text:
        return html_to_text(html_text)

    return ""