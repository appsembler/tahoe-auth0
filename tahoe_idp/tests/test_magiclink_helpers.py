from datetime import timedelta

import pytest
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.http import HttpRequest
from django.utils import timezone

from tahoe_idp.magiclink_helpers import create_magiclink, is_studio_allowed_for_user
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
        expiry = timezone.now() + timedelta(seconds=settings.MAGICLINK_AUTH_TIMEOUT)
        request = HttpRequest()
        magic_link = create_magiclink(username, request)
    assert magic_link.username == username
    assert len(magic_link.token) == settings.MAGICLINK_TOKEN_LENGTH
    assert magic_link.expiry == expiry
    assert magic_link.redirect_url == settings.LOGIN_REDIRECT_URL


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
    assert magic_link.used is False

    with patch_current_time('2000-01-01T00:00:31'):
        create_magiclink(username, request)

    magic_link = MagicLink.objects.get(token=magic_link.token)
    assert magic_link.used is True
    assert magic_link.username == username


@pytest.mark.django_db
def test_create_magiclink_login_request_time_limit():
    username = 'test_user'
    request = HttpRequest()
    create_magiclink(username, request)
    with pytest.raises(MagicLinkError):
        create_magiclink(username, request)


@pytest.mark.django_db
@pytest.mark.parametrize('is_staff,is_superuser,expected_result', [
    (False, False, False),
    (False, True, True),
    (True, False, True),
    (True, True, True),
])
def test_is_studio_allowed_for_user_no_external(is_staff, is_superuser, expected_result, settings, user):  # NOQA: F811
    """
    Verify that is_studio_allowed_for_user will check for staff and superuser if no external method is set
    """
    assert settings.MAGICLINK_STUDIO_PERMISSION_METHOD is None
    assert not is_studio_allowed_for_user(user)

    user.is_staff = is_staff
    user.is_superuser = is_superuser
    user.save()
    assert is_studio_allowed_for_user(user) == expected_result


@pytest.mark.django_db
def test_is_studio_allowed_for_user_with_external(settings, user):  # NOQA: F811
    """
    Verify that is_studio_allowed_for_user will check using the given external method
    """
    settings.MAGICLINK_STUDIO_PERMISSION_METHOD = 'tahoe_idp.tests.magiclink_fixtures:external_method_testing'

    assert not is_studio_allowed_for_user(user)
    user.email = 'permitted@example.com'
    user.save()
    assert is_studio_allowed_for_user(user)


@pytest.mark.django_db
def test_is_studio_allowed_for_user_with_failing_external(settings, user):  # NOQA: F811
    """
    Verify that is_studio_allowed_for_user will check using the given external method
    """
    settings.MAGICLINK_STUDIO_PERMISSION_METHOD = 'external_module.does_not:exists'

    with patch('tahoe_idp.magiclink_helpers.log.warning') as mock_log:
        assert not is_studio_allowed_for_user(user)
    mock_log.assert_called_once_with(
        "tahoue_idp.is_studio_allowed_for_user failed for user test_user: No module named 'external_module'"
    )
