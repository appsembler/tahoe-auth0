import pytest
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.urls import reverse, reverse_lazy

from tahoe_idp.tests.magiclink_fixtures import user  # NOQA: F401

User = get_user_model()


@pytest.mark.django_db
def test_studio_login_must_be_authenticated(client, settings):  # NOQA: F811
    url = reverse('studio_login')
    response = client.get(url)

    assert response.status_code == 302
    assert response.url.startswith(settings.LOGIN_URL)


@pytest.mark.django_db
def test_studio_login_must_be_permitted(settings, client, user):  # NOQA: F811
    url = reverse('studio_login')
    client.login(username=user.username, password='password')
    response = client.get(url)

    assert response.status_code == 404


@pytest.mark.django_db
@patch('tahoe_idp.magiclink_views.is_studio_allowed_for_user', Mock(return_value=True))
@pytest.mark.parametrize('studio_login_url', [
    reverse_lazy('studio_login'),
    '/studio',
    '/studio/',
])
def test_studio_login(settings, client, user, studio_login_url):  # NOQA: F811
    client.login(username=user.username, password='password')
    response = client.get(studio_login_url)

    assert response.status_code == 302
    assert response.url.startswith('http://{studio_domain}'.format(studio_domain=settings.MAGICLINK_STUDIO_DOMAIN))
