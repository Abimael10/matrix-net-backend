import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from src.config import config


def send_email(subject: str, recipient: str, body: str):
    """
    Sends an email using the Mailtrap SMTP configuration.

    Args:
        subject (str): The subject of the email.
        recipient (str): The recipient's email address.
        body (str): The HTML body of the email.
    """
    # Create the email message
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = config.MAIL_FROM
    msg["To"] = recipient

    # Create the plain-text and HTML version of your message
    text = f"Hello, please confirm your email by clicking the link: {body}"

    # Attach parts into message container.
    # The email client will try to render the last part first
    msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(body, "html"))

    # Debug: Print config and recipient info before sending
    print("--- Email Debug Info ---")
    print(f"MAIL_SERVER: {config.MAIL_SERVER}")
    print(f"MAIL_PORT: {config.MAIL_PORT}")
    print(f"MAIL_USERNAME: {config.MAIL_USERNAME}")
    print(f"MAIL_FROM: {config.MAIL_FROM}")
    print(f"Recipient: {recipient}")
    print(f"Subject: {subject}")
    print("------------------------")

    # Connect to Mailtrap and send the email
    try:
        with smtplib.SMTP(config.MAIL_SERVER, config.MAIL_PORT) as server:
            server.starttls()
            server.login(config.MAIL_USERNAME, config.MAIL_PASSWORD)
            server.sendmail(config.MAIL_FROM, recipient, msg.as_string())
        print("Email sent successfully.")
    except smtplib.SMTPException as e:
        print(f"Error sending email: {e}")
        raise
