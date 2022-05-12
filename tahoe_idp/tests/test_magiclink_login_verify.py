from importlib import reload
from urllib.parse import urlencode

import pytest
from django.contrib.auth import get_user_model
from django.http import HttpRequest
from django.http.cookie import SimpleCookie
from django.urls import reverse

from tahoe_idp.tests.magiclink_fixtures import magic_link, user  # NOQA: F401

User = get_user_model()


@pytest.mark.django_db
def test_login_verify(client, settings, magic_link):  # NOQA: F811
    url = reverse('tahoe_idp:login_verify')
    request = HttpRequest()
    ml = magic_link(request)
    ml.ip_address = '127.0.0.0'  # This is a little hacky
    ml.save()

    params = {'token': ml.token}
    params['email'] = ml.email
    query = urlencode(params)
    url = '{url}?{query}'.format(url=url, query=query)

    cookie_name = 'magiclink{pk}'.format(pk=ml.pk)
    client.cookies = SimpleCookie({cookie_name: ml.cookie_value})
    response = client.get(url)
    assert response.status_code == 302
    assert response.url == reverse(settings.LOGIN_REDIRECT_URL)
    assert client.cookies[cookie_name].value == ''
    assert client.cookies[cookie_name]['expires'].startswith('Thu, 01 Jan 1970')  # NOQA: E501

    needs_login_url = reverse('needs_login')
    needs_login_response = client.get(needs_login_url)
    assert needs_login_response.status_code == 200


@pytest.mark.django_db
def test_login_verify_with_redirect(client, magic_link):  # NOQA: F811
    url = reverse('tahoe_idp:login_verify')
    request = HttpRequest()
    request.META['SERVER_NAME'] = '127.0.0.1'
    request.META['SERVER_PORT'] = 80
    ml = magic_link(request)
    ml.ip_address = '127.0.0.0'  # This is a little hacky
    redirect_url = reverse('no_login')
    ml.redirect_url = redirect_url
    ml.save()
    url = ml.generate_url(request)

    client.cookies = SimpleCookie({'magiclink{pk}'.format(pk=ml.pk): ml.cookie_value})
    response = client.get(url)
    assert response.status_code == 302
    assert response.url == redirect_url


@pytest.mark.django_db
def test_login_verify_no_token_404(client, settings):
    settings.MAGICLINK_LOGIN_FAILED_TEMPLATE_NAME = ''
    from tahoe_idp import magiclink_settings as mlsettings
    reload(mlsettings)

    url = reverse('tahoe_idp:login_verify')
    response = client.get(url)
    assert response.status_code == 404


@pytest.mark.django_db
def test_login_verify_failed(client, settings):
    settings.MAGICLINK_LOGIN_FAILED_TEMPLATE_NAME = 'tahoe_idp/magiclink_login_failed.html'  # NOQA: E501
    from tahoe_idp import magiclink_settings as mlsettings
    reload(mlsettings)

    url = reverse('tahoe_idp:login_verify')
    response = client.get(url)
    assert response.status_code == 200
    context = response.context_data
    assert context['login_error'] == 'A magic link with that token could not be found'  # NOQA: E501


@pytest.mark.django_db
def test_login_verify_failed_validation(client, settings, magic_link):  # NOQA: F811,E501
    settings.MAGICLINK_LOGIN_FAILED_TEMPLATE_NAME = 'tahoe_idp/magiclink_login_failed.html'  # NOQA: E501
    from tahoe_idp import magiclink_settings as mlsettings
    reload(mlsettings)

    url = reverse('tahoe_idp:login_verify')
    request = HttpRequest()
    ml = magic_link(request)
    params = {'token': ml.token}
    params['email'] = ml.email
    query = urlencode(params)
    url = '{url}?{query}'.format(url=url, query=query)

    response = client.get(url)
    assert response.status_code == 200
    context = response.context_data
    assert context['login_error'] == 'IP address is different from the IP address used to request the magic link'  # NOQA: E501


@pytest.mark.django_db
def test_login_verify_failed_redirect(client, settings):
    fail_redirect_url = '/failedredirect'
    settings.MAGICLINK_LOGIN_FAILED_REDIRECT = fail_redirect_url
    from tahoe_idp import magiclink_settings as mlsettings
    reload(mlsettings)

    url = reverse('tahoe_idp:login_verify')
    response = client.get(url)
    assert response.url == fail_redirect_url


@pytest.mark.django_db
def test_login_verify_custom_verify(client, settings, magic_link):  # NOQA: F811,E501
    settings.MAGICLINK_LOGIN_VERIFY_URL = 'custom_login_verify'
    from tahoe_idp import magiclink_settings as settings
    reload(settings)

    url = reverse(settings.LOGIN_VERIFY_URL)
    request = HttpRequest()
    request.META['SERVER_NAME'] = '127.0.0.1'
    request.META['SERVER_PORT'] = 80
    ml = magic_link(request)
    ml.ip_address = '127.0.0.0'
    ml.redirect_url = reverse('needs_login')  # Should be ignored
    ml.save()
    url = ml.generate_url(request)

    cookie_name = 'magiclink{pk}'.format(pk=ml.pk)
    client.cookies = SimpleCookie({cookie_name: ml.cookie_value})
    response = client.get(url)
    assert response.status_code == 302
    assert response.url == reverse('no_login')
    assert client.cookies[cookie_name].value == ''
    assert client.cookies[cookie_name]['expires'].startswith('Thu, 01 Jan 1970')  # NOQA: E501

    settings.MAGICLINK_LOGIN_VERIFY_URL = 'tahoe_idp:login_verify'
    from tahoe_idp import magiclink_settings as settings
    reload(settings)
