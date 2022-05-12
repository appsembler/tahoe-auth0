from datetime import timedelta
from importlib import reload
from urllib.parse import quote

import pytest
from django.contrib.auth import get_user_model
from django.http import HttpRequest
from django.urls import reverse
from django.utils import timezone

from tahoe_idp import magiclink_settings as settings
from tahoe_idp.models import MagicLink, MagicLinkError

from tahoe_idp.tests.magiclink_fixtures import magic_link, user  # NOQA: F401

User = get_user_model()


def get_magic_link_verifying_list(host, login_url, token, email):
    return [
        'http://{host}{login_url}?token={token}&email={email}'.format(
            host=host,
            login_url=login_url,
            token=token,
            email=quote(email),
        ),
        'http://{host}{login_url}?email={email}&token={token}'.format(
            host=host,
            login_url=login_url,
            token=token,
            email=quote(email),
        )
    ]


@pytest.mark.django_db
def test_model_string(magic_link):  # NOQA: F811
    request = HttpRequest()
    ml = magic_link(request)
    assert str(ml) == '{email} - {expiry}'.format(email=ml.email, expiry=ml.expiry)


@pytest.mark.django_db
def test_generate_url(settings, magic_link):  # NOQA: F811
    settings.MAGICLINK_LOGIN_VERIFY_URL = 'tahoe_idp:login_verify'
    from tahoe_idp import magiclink_settings as settings
    reload(settings)

    request = HttpRequest()
    host = settings.STUDIO_DOMAIN
    login_url = reverse('tahoe_idp:login_verify')
    request.META['SERVER_NAME'] = host
    request.META['SERVER_PORT'] = 80
    ml = magic_link(request)
    assert ml.generate_url(request) in get_magic_link_verifying_list(host, login_url, ml.token, ml.email)


@pytest.mark.django_db
def test_generate_url_custom_verify(settings, magic_link):  # NOQA: F811
    settings.MAGICLINK_LOGIN_VERIFY_URL = 'custom_login_verify'
    from tahoe_idp import magiclink_settings as settings
    reload(settings)

    request = HttpRequest()
    host = settings.STUDIO_DOMAIN
    login_url = reverse('custom_login_verify')
    request.META['SERVER_NAME'] = host
    request.META['SERVER_PORT'] = 80
    ml = magic_link(request)
    assert ml.generate_url(request) in get_magic_link_verifying_list(host, login_url, ml.token, ml.email)
    settings.MAGICLINK_LOGIN_VERIFY_URL = 'tahoe_idp:login_verify'
    from tahoe_idp import magiclink_settings as settings
    reload(settings)


@pytest.mark.django_db
def test_validate(user, magic_link):  # NOQA: F811
    request = HttpRequest()
    ml = magic_link(request)
    request.COOKIES['magiclink{pk}'.format(pk=ml.pk)] = ml.cookie_value
    ml_user = ml.validate(request=request, email=user.email)
    assert ml_user == user


@pytest.mark.django_db
def test_validate_email_ignore_case(user, magic_link):  # NOQA: F811
    request = HttpRequest()
    ml = magic_link(request)
    request.COOKIES['magiclink{pk}'.format(pk=ml.pk)] = ml.cookie_value
    ml_user = ml.validate(request=request, email=user.email.upper())
    assert ml_user == user


@pytest.mark.django_db
def test_validate_wrong_email(user, magic_link):  # NOQA: F811
    request = HttpRequest()
    ml = magic_link(request)
    email = 'fake@email.com'
    request.COOKIES['magiclink{pk}'.format(pk=ml.pk)] = ml.cookie_value
    with pytest.raises(MagicLinkError) as error:
        ml.validate(request=request, email=email)

    error.match('Email address does not match')


@pytest.mark.django_db
def test_validate_expired(user, magic_link):  # NOQA: F811
    request = HttpRequest()
    ml = magic_link(request)
    request.COOKIES['magiclink{pk}'.format(pk=ml.pk)] = ml.cookie_value
    ml.expiry = timezone.now() - timedelta(seconds=1)
    ml.save()

    with pytest.raises(MagicLinkError) as error:
        ml.validate(request=request, email=user.email)

    error.match('Magic link has expired')

    ml = MagicLink.objects.get(token=ml.token)
    assert ml.times_used == 1
    assert ml.disabled is True


@pytest.mark.django_db
def test_validate_wrong_ip(user, magic_link):  # NOQA: F811
    request = HttpRequest()
    ml = magic_link(request)
    request.COOKIES['magiclink{pk}'.format(pk=ml.pk)] = ml.cookie_value
    ml.ip_address = '255.255.255.255'
    ml.save()
    with pytest.raises(MagicLinkError) as error:
        ml.validate(request=request, email=user.email)

    error.match('IP address is different from the IP address used to request '
                'the magic link')

    ml = MagicLink.objects.get(token=ml.token)
    assert ml.times_used == 1
    assert ml.disabled is True


@pytest.mark.django_db
def test_validate_different_browser(user, magic_link):  # NOQA: F811
    request = HttpRequest()
    ml = magic_link(request)
    request.COOKIES['magiclink{pk}'.format(pk=ml.pk)] = 'bad_value'
    with pytest.raises(MagicLinkError) as error:
        ml.validate(request=request, email=user.email)

    error.match('Browser is different from the browser used to request the '
                'magic link')

    ml = MagicLink.objects.get(token=ml.token)
    assert ml.times_used == 1
    assert ml.disabled is True


@pytest.mark.django_db
def test_validate_used_times(user, magic_link):  # NOQA: F811
    request = HttpRequest()
    ml = magic_link(request)
    request.COOKIES['magiclink{pk}'.format(pk=ml.pk)] = ml.cookie_value
    ml.times_used = settings.TOKEN_USES
    ml.save()
    with pytest.raises(MagicLinkError) as error:
        ml.validate(request=request, email=user.email)

    error.match('Magic link has been used too many times')

    ml = MagicLink.objects.get(token=ml.token)
    assert ml.times_used == settings.TOKEN_USES + 1
    assert ml.disabled is True


@pytest.mark.django_db
def test_validate_superuser(settings, user, magic_link):  # NOQA: F811
    settings.MAGICLINK_ALLOW_SUPERUSER_LOGIN = False
    from tahoe_idp import magiclink_settings as settings
    reload(settings)

    request = HttpRequest()
    ml = magic_link(request)
    request.COOKIES['magiclink{pk}'.format(pk=ml.pk)] = ml.cookie_value
    user.is_superuser = True
    user.save()
    with pytest.raises(MagicLinkError) as error:
        ml.validate(request=request, email=user.email)

    error.match('You can not login to a super user account using a magic link')

    ml = MagicLink.objects.get(token=ml.token)
    assert ml.times_used == 1
    assert ml.disabled is True


@pytest.mark.django_db
def test_validate_staff(settings, user, magic_link):  # NOQA: F811
    settings.MAGICLINK_ALLOW_STAFF_LOGIN = False
    from tahoe_idp import magiclink_settings as settings
    reload(settings)

    request = HttpRequest()
    ml = magic_link(request)
    request.COOKIES['magiclink{pk}'.format(pk=ml.pk)] = ml.cookie_value
    user.is_staff = True
    user.save()
    with pytest.raises(MagicLinkError) as error:
        ml.validate(request=request, email=user.email)

    error.match('You can not login to a staff account using a magic link')

    ml = MagicLink.objects.get(token=ml.token)
    assert ml.times_used == 1
    assert ml.disabled is True
