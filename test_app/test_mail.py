"""
Testing email sending functions for User verification flows
"""

from collections import namedtuple
from smtplib import SMTP_SSL, SMTPAuthenticationError

from app.mail import get_smtp, send_password_reset
from pytest import raises


def test_get_smtp():
    """Test app.mail.get_smtp()"""
    with raises(Exception) as _:
        with get_smtp() as smtp_ssl:
            assert isinstance(smtp_ssl, SMTP_SSL)


def test_send_password_reset():
    """Test app.mail.send_password_reset()"""
    TestUser = namedtuple('User', ['b64_access_token', 'email'])
    test_user = TestUser(b'123', 'test@findteam.2labz.com')
    with raises(SMTPAuthenticationError) as _:
        send_password_reset(test_user)
