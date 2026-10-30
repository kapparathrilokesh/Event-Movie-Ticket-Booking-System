
import logging

logger = logging.getLogger("email_notifications")


async def send_email(
    recipient: str,
    subject: str,
    body: str,
) -> bool:
    """Print a development email preview to the application terminal."""
    message = (
        "\n========== EMAIL NOTIFICATION ==========\n"
        f"To: {recipient}\n"
        f"Subject: {subject}\n"
        f"Message:\n{body}\n"
        "========================================"
    )

    print(message, flush=True)
    logger.info(message)

    return True
