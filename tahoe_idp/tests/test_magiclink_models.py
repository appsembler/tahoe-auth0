from datetime import timedelta
from urllib.parse import quote

import pytest
from django.contrib.auth import get_user_model
from django.http import HttpRequest
from django.urls import reverse
from django.utils import timezone

from tahoe_idp.models import MagicLink, MagicLinkError

from tahoe_idp.tests.magiclink_fixtures import magic_link, user  # NOQA: F401

User = get_user_model()


def get_magic_link_verifying_list(host, login_url, token, username):
    return [
        'http://{host}{login_url}?token={token}&username={username}'.format(
            host=host,
            login_url=login_url,
            token=token,
            username=quote(username),
        ),
        'http://{host}{login_url}?username={username}&token={token}'.format(
            host=host,
            login_url=login_url,
            token=token,
            username=quote(username),
        )
    ]


@pytest.mark.django_db
def test_model_string(magic_link):  # NOQA: F811
    request = HttpRequest()
    ml = magic_link(request)
    assert str(ml) == '{username} - {expiry}'.format(username=ml.username, expiry=ml.expiry)


@pytest.mark.django_db
def test_generate_url(settings, magic_link):  # NOQA: F811
    settings.LOGIN_VERIFY_URL = 'tahoe_idp:login_verify'

    request = HttpRequest()
    host = settings.STUDIO_DOMAIN
    login_url = reverse('tahoe_idp:login_verify')
    request.META['SERVER_NAME'] = host
    request.META['SERVER_PORT'] = 80
    ml = magic_link(request)
    assert ml.generate_url(request) in get_magic_link_verifying_list(host, login_url, ml.token, ml.username)


@pytest.mark.django_db
def test_generate_url_custom_verify(settings, magic_link):  # NOQA: F811
    settings.LOGIN_VERIFY_URL = 'custom_login_verify'

    request = HttpRequest()
    host = settings.STUDIO_DOMAIN
    login_url = reverse('custom_login_verify')
    request.META['SERVER_NAME'] = host
    request.META['SERVER_PORT'] = 80
    ml = magic_link(request)
    assert ml.generate_url(request) in get_magic_link_verifying_list(host, login_url, ml.token, ml.username)


@pytest.mark.django_db
def test_validate(user, magic_link):  # NOQA: F811
    request = HttpRequest()
    ml = magic_link(request)
    assert user == ml.get_user_with_validate(request=request, username=user.username)


@pytest.mark.django_db
def test_validate_wrong_username(user, magic_link):  # NOQA: F811
    request = HttpRequest()
    ml = magic_link(request)
    username = 'fake_username'
    with pytest.raises(MagicLinkError) as error:
        ml.get_user_with_validate(request=request, username=username)

    error.match('username does not match')


@pytest.mark.django_db
def test_validate_expired(user, magic_link):  # NOQA: F811
    request = HttpRequest()
    ml = magic_link(request)
    ml.expiry = timezone.now() - timedelta(seconds=1)
    ml.save()

    with pytest.raises(MagicLinkError) as error:
        ml.get_user_with_validate(request=request, username=user.username)

    error.match('Magic link has expired')

    ml = MagicLink.objects.get(token=ml.token)
    assert ml.used is True


@pytest.mark.django_db
def test_validate_used_times(user, magic_link):  # NOQA: F811
    request = HttpRequest()
    ml = magic_link(request)
    ml.used = True
    ml.save()
    with pytest.raises(MagicLinkError) as error:
        ml.get_user_with_validate(request=request, username=user.username)

    error.match('Magic link already used')
