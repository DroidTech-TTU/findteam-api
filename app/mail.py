from email.message import EmailMessage
from smtplib import SMTP_SSL
from urllib.parse import urlencode

from .config import get_settings
from .models import User

_settings = get_settings()
address = _settings.email_address
password = _settings.email_password


def send_password_reset(user: User):
    """Send password reset email to User via FindTeam gmail SMTP"""
    msg = EmailMessage()
    # TODO: Fill in Android password reset URI
    reset_uri = f'findteam://forgot?{urlencode({"access_token": user.b64_access_token.decode()})}'
    msg.set_content(
        f'Hello - the link to reset your password is here: {reset_uri}')
    msg['Subject'] = 'FindTeam Password Reset'
    msg['From'] = address
    msg['To'] = user.email
    with get_smtp() as smtp:
        smtp.send_message(msg)


def get_smtp() -> SMTP_SSL:
    """Authenticate with mail server using config, returning connection"""
    smtp = SMTP_SSL(
        host='smtp.gmail.com',
        local_hostname='findteam.2labz.com')
    smtp.login(address, password)
    return smtp
