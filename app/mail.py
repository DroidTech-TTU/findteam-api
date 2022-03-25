"""
Email sending functions for User verification flows
"""

from email.message import EmailMessage
from smtplib import SMTP_SSL
from urllib.parse import urlencode

from jinja2 import Environment, FileSystemLoader

from .config import get_settings
from .models import User

_settings = get_settings()
address = _settings.email_address
password = _settings.email_password
jinja2 = Environment(loader=FileSystemLoader(_settings.template_path))
forgot_template = jinja2.get_template('email_forgot_link.html')


def send_password_reset(user: User) -> None:
    """Send password reset email to User via FindTeam gmail SMTP"""
    reset_uri = f'https://findteam.2labz.com/forgot?{urlencode({"access_token": user.b64_access_token.decode()})}'
    msg = EmailMessage()
    msg.set_type('text/html')
    msg.set_content(reset_uri)
    msg.add_alternative(forgot_template.render(
        reset_uri=reset_uri), subtype='html')
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
