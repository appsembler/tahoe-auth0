from datetime import timedelta
from importlib import reload

import pytest
from django.contrib.auth import get_user_model
# from django.db import models
from django.http import HttpRequest
from django.urls import reverse
from django.utils import timezone

from tahoe_idp import magiclink_settings as mlsettings
from tahoe_idp.magiclink_helpers import create_magiclink, get_or_create_user
from tahoe_idp.models import MagicLink, MagicLinkError

from tahoe_idp.tests.magiclink_fixtures import user  # NOQA: F401

User = get_user_model()

# import factory
from django.contrib.auth.models import AbstractUser
from django.db import models



class CustomUserEmailOnly(AbstractUser):
    email = models.EmailField('email address', unique=True)


class CustomUserFullName(CustomUserEmailOnly):
    full_name = models.TextField()


class CustomUserName(CustomUserEmailOnly):
    name = models.TextField()

# class CustomUserEmailOnly(factory.django.DjangoModelFactory):
#     """
#     Factory helper for tests
#     """
#     email = models.EmailField('email address', unique=True)
#     username = factory.Sequence('robot{}'.format)
#
#     class Meta:
#         model = get_user_model()
#
#
# class CustomUserFullName(CustomUserEmailOnly):
#     full_name = models.TextField()
#
#
# class CustomUserName(CustomUserEmailOnly):
#     name = models.TextField()


@pytest.mark.django_db
def test_create_magiclink(settings, freezer):
    freezer.move_to('2000-01-01T00:00:00')

    email = 'test@example.com'
    expiry = timezone.now() + timedelta(seconds=mlsettings.AUTH_TIMEOUT)
    request = HttpRequest()
    request.META['REMOTE_ADDR'] = '127.0.0.1'
    magic_link = create_magiclink(email, request)
    assert magic_link.email == email
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
    magic_link = create_magiclink('test@example.com', request)
    assert magic_link.ip_address is None


@pytest.mark.django_db
def test_create_magiclink_none_anonymized_ip(settings):
    settings.MAGICLINK_ANONYMIZE_IP = False
    from tahoe_idp import magiclink_settings as mlsettings
    reload(mlsettings)

    request = HttpRequest()
    ip_address = '127.0.0.1'
    request.META['REMOTE_ADDR'] = ip_address
    magic_link = create_magiclink('test@example.com', request)
    assert magic_link.ip_address == ip_address


@pytest.mark.django_db
def test_create_magiclink_redirect_url():
    email = 'test@example.com'
    request = HttpRequest()
    redirect_url = '/test/'
    magic_link = create_magiclink(email, request, redirect_url=redirect_url)
    assert magic_link.email == email
    assert magic_link.redirect_url == redirect_url


@pytest.mark.django_db
def test_create_magiclink_email_ignore_case():
    email = 'TEST@example.com'
    request = HttpRequest()
    magic_link = create_magiclink(email, request)
    assert magic_link.email == email.lower()


@pytest.mark.django_db
def test_create_magiclink_email_ignore_case_off(settings):
    settings.MAGICLINK_EMAIL_IGNORE_CASE = False
    from tahoe_idp import magiclink_settings as settings
    reload(settings)

    email = 'TEST@example.com'
    request = HttpRequest()
    magic_link = create_magiclink(email, request)
    assert magic_link.email == email


@pytest.mark.django_db
def test_create_magiclink_one_token_per_user(freezer):
    email = 'test@example.com'
    request = HttpRequest()
    freezer.move_to('2000-01-01T00:00:00')
    magic_link = create_magiclink(email, request)
    assert magic_link.disabled is False

    freezer.move_to('2000-01-01T00:00:31')
    create_magiclink(email, request)

    magic_link = MagicLink.objects.get(token=magic_link.token)
    assert magic_link.disabled is True
    assert magic_link.email == email


@pytest.mark.django_db
def test_create_magiclink_login_request_time_limit():
    email = 'test@example.com'
    request = HttpRequest()
    create_magiclink(email, request)
    with pytest.raises(MagicLinkError):
        create_magiclink(email, request)


@pytest.mark.django_db
def test_get_or_create_user_exists(user):  # NOQA: F811
    usr = get_or_create_user(email=user.email)
    assert usr == user
    assert User.objects.count() == 1


@pytest.mark.django_db
def test_get_or_create_user_exists_ignore_case(settings, user):  # NOQA: F811
    settings.MAGICLINK_EMAIL_IGNORE_CASE = True
    from tahoe_idp import magiclink_settings as settings
    reload(settings)

    usr = get_or_create_user(email=user.email.upper())
    assert usr == user
    assert User.objects.count() == 1


@pytest.mark.django_db
def test_get_or_create_user_email_as_username():
    email = 'test@example.com'
    usr = get_or_create_user(email=email)
    assert usr.email == email
    assert usr.username == email


@pytest.mark.django_db
def test_get_or_create_user_random_username(settings):
    settings.MAGICLINK_EMAIL_AS_USERNAME = False
    from tahoe_idp import magiclink_settings as settings
    reload(settings)

    email = 'test@example.com'
    usr = get_or_create_user(email=email)
    assert usr.email == email
    assert usr.username != email
    assert len(usr.username) == 10


@pytest.mark.django_db
def test_get_or_create_user_first_name():
    first_name = 'fname'
    usr = get_or_create_user(email='test@example.com', first_name=first_name)
    assert usr.first_name == first_name


@pytest.mark.django_db
def test_get_or_create_user_last_name():
    last_name = 'lname'
    usr = get_or_create_user(email='test@example.com', last_name=last_name)
    assert usr.last_name == last_name


@pytest.mark.django_db
def test_get_or_create_user_no_username(mocker):
    gum = mocker.patch('tahoe_idp.magiclink_helpers.get_user_model')
    gum.return_value = CustomUserEmailOnly

    from tahoe_idp.magiclink_helpers import get_or_create_user
    email = 'test@example.com'
    usr = get_or_create_user(email=email)
    assert usr.email == email


@pytest.mark.django_db
def test_get_or_create_user_full_name(mocker):
    gum = mocker.patch('tahoe_idp.magiclink_helpers.get_user_model')
    gum.return_value = CustomUserFullName

    from tahoe_idp.magiclink_helpers import get_or_create_user
    email = 'test@example.com'
    first = 'fname'
    last = 'lname'
    usr = get_or_create_user(email=email, first_name=first, last_name=last)
    assert usr.email == email
    assert usr.full_name == '{first} {last}'.format(first=first, last=last)


@pytest.mark.django_db
def test_get_or_create_user_name(mocker):
    gum = mocker.patch('tahoe_idp.magiclink_helpers.get_user_model')
    gum.return_value = CustomUserName

    from tahoe_idp.magiclink_helpers import get_or_create_user
    email = 'test@example.com'
    first = 'fname'
    last = 'lname'
    usr = get_or_create_user(email=email, first_name=first, last_name=last)
    assert usr.email == email
    assert usr.name == '{first} {last}'.format(first=first, last=last)
