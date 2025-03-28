import requests
from flask import current_app

def send_mailgun_email(recipient, subject, body):
    """Send an email using Mailgun."""
    MAILGUN_DOMAIN = current_app.config.get("MAILGUN_DOMAIN")
    MAILGUN_API_KEY = current_app.config.get("MAILGUN_API_KEY")
    SENDER_EMAIL = current_app.config.get("SENDER_EMAIL")
    
    response = requests.post(
        f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
        auth=("api", MAILGUN_API_KEY),
        data={
            "from": f"Password Reset <{SENDER_EMAIL}>",
            "to": recipient,
            "subject": subject,
            "text": body
        }
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.text}")
    return response