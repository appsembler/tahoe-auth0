import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from tahoe_idp.tests.magiclink_fixtures import user  # NOQA: F401

User = get_user_model()


@pytest.mark.django_db
def test_studio_login_must_be_authenticated(client, settings):  # NOQA: F811
    url = reverse('studio_login')
    response = client.get(url)

    assert response.status_code == 302
    assert response.url.startswith(settings.LOGIN_URL)


@pytest.mark.django_db
def test_studio_login(settings, client, user):  # NOQA: F811
    url = reverse('studio_login')
    client.login(username=user.username, password='password')
    response = client.get(url)

    assert response.status_code == 302
    assert response.url.startswith('http://{studio_domain}'.format(studio_domain=settings.MAGICLINK_STUDIO_DOMAIN))
