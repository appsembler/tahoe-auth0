from urllib.parse import urlencode

import pytest
from django.contrib.auth import get_user_model
from django.http import HttpRequest
from django.urls import reverse

from tahoe_idp.tests.magiclink_fixtures import magic_link, user  # NOQA: F401


User = get_user_model()


@pytest.mark.django_db
def test_login_verify(client, settings, magic_link):  # NOQA: F811
    url = reverse('tahoe_idp:login_verify')
    request = HttpRequest()
    ml = magic_link(request)
    ml.save()

    params = {'token': ml.token}
    params['username'] = ml.username
    query = urlencode(params)
    url = '{url}?{query}'.format(url=url, query=query)

    response = client.get(url)
    assert response.status_code == 302
    assert response.url == settings.LOGIN_REDIRECT_URL

    needs_login_url = reverse('needs_login')
    needs_login_response = client.get(needs_login_url)
    assert needs_login_response.status_code == 200


@pytest.mark.django_db
def test_login_verify_with_redirect(client, magic_link):  # NOQA: F811
    request = HttpRequest()
    ml = magic_link(request)
    redirect_url = reverse('no_login')
    ml.redirect_url = redirect_url
    ml.save()
    url = ml.generate_url(request)

    response = client.get(url)
    assert response.status_code == 302
    assert response.url == redirect_url


@pytest.mark.django_db
def test_login_verify_failed_not_found(client, settings):
    fail_redirect_url = '/failedredirect'
    settings.MAGICLINK_LOGIN_FAILED_REDIRECT = fail_redirect_url

    url = reverse('tahoe_idp:login_verify')
    params = {'token': 'does not matter', 'username': 'does not matter'}
    query = urlencode(params)
    url = '{url}?{query}'.format(url=url, query=query)
    response = client.get(url)

    assert response.status_code == 302
    assert response.url == fail_redirect_url


@pytest.mark.django_db
def test_login_verify_failed_redirect(client, settings):
    fail_redirect_url = '/failedredirect'
    settings.MAGICLINK_LOGIN_FAILED_REDIRECT = fail_redirect_url

    url = reverse('tahoe_idp:login_verify')
    params = {'token': 'does not matter', 'username': 'does not matter'}
    query = urlencode(params)
    url = '{url}?{query}'.format(url=url, query=query)

    response = client.get(url)
    assert response.url == fail_redirect_url


@pytest.mark.django_db
def test_login_verify_custom_verify(client, settings, magic_link):  # NOQA: F811,E501
    settings.MAGICLINK_LOGIN_VERIFY_URL = 'custom_login_verify'

    request = HttpRequest()
    ml = magic_link(request)
    ml.redirect_url = reverse('needs_login')  # Should be ignored
    ml.save()
    url = ml.generate_url(request)

    response = client.get(url)
    assert response.status_code == 302
    assert response.url == reverse('no_login')
