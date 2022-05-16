import pytest
from django.contrib.auth import get_user_model

from tahoe_idp.magiclink_helpers import create_magiclink

User = get_user_model()


@pytest.fixture()
def user():
    return User.objects.create(
        email='test@example.com',
        username='test_user'
    )


@pytest.fixture
def magic_link(user):

    def _create(request):
        return create_magiclink(user.username, request, redirect_url='')

    return _create
