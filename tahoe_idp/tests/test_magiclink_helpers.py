from datetime import timedelta
from importlib import reload

import pytest
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.http import HttpRequest
from django.urls import reverse
from django.utils import timezone

from tahoe_idp import magiclink_settings as mlsettings
from tahoe_idp.magiclink_helpers import create_magiclink
from tahoe_idp.models import MagicLink, MagicLinkError
from tahoe_idp.tests.magiclink_fixtures import user  # NOQA: F401


User = get_user_model()


class CustomUserEmailOnly(AbstractUser):
    email = models.EmailField('email address', unique=True)


class CustomUserFullName(CustomUserEmailOnly):
    full_name = models.TextField()


class CustomUserName(CustomUserEmailOnly):
    name = models.TextField()


def patch_current_time(datetime_string):
    if len(datetime_string) == 10:
        datetime_string += ' 00:00:00'
    dt = timezone.make_aware(timezone.datetime.strptime(datetime_string, '%Y-%m-%dT%H:%M:%S'))
    return patch('django.utils.timezone.now', return_value=dt)


@pytest.mark.django_db
def test_create_magiclink(settings):
    with patch_current_time('2000-01-01T00:00:00'):
        username = 'test_user'
        expiry = timezone.now() + timedelta(seconds=mlsettings.AUTH_TIMEOUT)
        request = HttpRequest()
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        magic_link = create_magiclink(username, request)
    assert magic_link.username == username
    assert len(magic_link.token) == mlsettings.TOKEN_LENGTH
    assert magic_link.expiry == expiry
    assert magic_link.redirect_url == reverse(settings.LOGIN_REDIRECT_URL)
    assert len(magic_link.cookie_value) == 36
    assert magic_link.ip_address == '127.0.0.0'  # Anonymize IP by default


@pytest.mark.django_db
def test_create_magiclink_require_same_ip_off_no_ip(settings):
    settings.MAGICLINK_REQUIRE_SAME_IP = False
    from tahoe_idp import magiclink_settings as mlsettings
    reload(mlsettings)

    request = HttpRequest()
    request.META['REMOTE_ADDR'] = '127.0.0.1'
    magic_link = create_magiclink('test_user', request)
    assert magic_link.ip_address is None


@pytest.mark.django_db
def test_create_magiclink_none_anonymized_ip(settings):
    settings.MAGICLINK_ANONYMIZE_IP = False
    from tahoe_idp import magiclink_settings as mlsettings
    reload(mlsettings)

    request = HttpRequest()
    ip_address = '127.0.0.1'
    request.META['REMOTE_ADDR'] = ip_address
    magic_link = create_magiclink('test_user', request)
    assert magic_link.ip_address == ip_address


@pytest.mark.django_db
def test_create_magiclink_redirect_url():
    username = 'test_user'
    request = HttpRequest()
    redirect_url = '/test/'
    magic_link = create_magiclink(username, request, redirect_url=redirect_url)
    assert magic_link.username == username
    assert magic_link.redirect_url == redirect_url


@pytest.mark.django_db
def test_create_magiclink_one_token_per_user():
    username = 'test_user'
    request = HttpRequest()

    with patch_current_time('2000-01-01T00:00:00'):
        magic_link = create_magiclink(username, request)
    assert magic_link.disabled is False

    with patch_current_time('2000-01-01T00:00:31'):
        create_magiclink(username, request)

    magic_link = MagicLink.objects.get(token=magic_link.token)
    assert magic_link.disabled is True
    assert magic_link.username == username


@pytest.mark.django_db
def test_create_magiclink_login_request_time_limit():
    username = 'test_user'
    request = HttpRequest()
    create_magiclink(username, request)
    with pytest.raises(MagicLinkError):
        create_magiclink(username, request)
