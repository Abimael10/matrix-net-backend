import logging
import httpx

from src.config import config

logger = logging.getLogger(__name__)


async def send_email(subject: str, recipient: str, body: str):
    """
    Sends an email using the Mailtrap API.

    Args:
        subject (str): The subject of the email.
        recipient (str): The recipient's email address.
        body (str): The HTML body of the email.
    """
    if not config.MAIL_API_TOKEN:
        logger.error("MAIL_API_TOKEN is not configured. Cannot send email.")
        return

    try:
        url = "https://send.api.mailtrap.io/"

        payload = {
            "from": {
                "email": config.MAIL_FROM,
                "name": config.MAIL_FROM_NAME
            },
            "to": [{"email": recipient}],
            "subject": subject,
            "html": body,
            "category": "Email Confirmation"
        }

        headers = {
            "Authorization": f"Bearer {config.MAIL_API_TOKEN}",
            "Content-Type": "application/json"
        }

        logger.info(f"Attempting to send email to {recipient} via Mailtrap API")

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()

        logger.info(f"Email sent successfully to {recipient}. Status: {response.status_code}")
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error sending email to {recipient}: {e.response.status_code} - {e.response.text}")
        # Don't raise - let registration succeed even if email fails
    except httpx.RequestError as e:
        logger.error(f"Request error sending email to {recipient}: {e}")
        # Don't raise - let registration succeed even if email fails
    except Exception as e:
        logger.error(f"Unexpected error sending email to {recipient}: {e}")
        # Don't raise - let registration succeed even if email fails
