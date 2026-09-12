import imaplib
import email

from datetime import datetime, timedelta
from email.message import Message

from app.core.config import settings


class EmailReader:

    def __init__(self):
        self.__host = "imap.gmail.com"
        self.__port = 993
        self.__username = settings.EMAIL
        self.__password = settings.APP_PASSWORD
        self.__folder = settings.GMAIL_FOLDER

    def read_emails(
        self,
        from_date: datetime,
        to_date: datetime,
    ) -> list[Message]:

        mail = None

        try:
            mail = self.__connect()

            # ---------------------------------------------------------
            # Select mailbox
            # ---------------------------------------------------------
            status, _ = mail.select(
                f'"{self.__folder}"',
                readonly=True,
            )

            if status != "OK":
                raise RuntimeError(
                    f"Unable to select Gmail folder: {self.__folder}"
                )

            # ---------------------------------------------------------
            # IMAP SEARCH works with dates, not timestamps.
            #
            # SINCE is inclusive.
            # BEFORE is exclusive.
            #
            # Therefore:
            # from_date = 10-Sep
            # to_date   = 10-Sep
            #
            # becomes:
            # SINCE 10-Sep-2026
            # BEFORE 11-Sep-2026
            # ---------------------------------------------------------
            since = from_date.strftime("%d-%b-%Y")

            before_date = to_date + timedelta(days=1)
            before = before_date.strftime("%d-%b-%Y")

            status, data = mail.search(
                None,
                f"SINCE {since}",
                f"BEFORE {before}",
            )

            if status != "OK":
                return []

            email_ids = data[0].split()

            print(f"Found {len(email_ids)} emails")

            messages: list[Message] = []

            # ---------------------------------------------------------
            # Fetch emails one by one
            # ---------------------------------------------------------
            for email_id in email_ids:

                try:
                    status, msg_data = mail.fetch(
                        email_id,
                        "(RFC822)",
                    )

                    if status != "OK":
                        print(
                            f"Unable to fetch email ID: {email_id.decode()}"
                        )
                        continue

                    raw_email = None

                    for response_part in msg_data:
                        if (
                            isinstance(response_part, tuple)
                            and len(response_part) >= 2
                        ):
                            raw_email = response_part[1]
                            break

                    if not raw_email:
                        print(
                            f"No email content found for ID: "
                            f"{email_id.decode()}"
                        )
                        continue

                    message = email.message_from_bytes(
                        raw_email
                    )

                    messages.append(message)

                except imaplib.IMAP4.abort as exc:
                    print(
                        f"IMAP connection aborted while fetching "
                        f"email {email_id.decode()}: {exc}"
                    )

                    # Stop processing because this connection is no
                    # longer usable.
                    break

            return messages

        finally:
            if mail is not None:
                try:
                    mail.close()
                except Exception:
                    pass

                try:
                    mail.logout()
                except Exception:
                    pass

    def __connect(self) -> imaplib.IMAP4_SSL:
        print("Connecting to Gmail IMAP...")

        mail = imaplib.IMAP4_SSL(
            self.__host,
            self.__port,
            timeout=30,
        )

        print("Logging into Gmail...")

        mail.login(
            self.__username,
            self.__password,
        )

        print("Gmail IMAP login successful")

        return mail