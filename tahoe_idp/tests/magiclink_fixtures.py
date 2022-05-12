import pytest
from django.contrib.auth import get_user_model

from tahoe_idp.magiclink_helpers import create_magiclink

User = get_user_model()


@pytest.fixture()
def user():
    email = 'test@example.com'
    return User.objects.create(email=email, username=email)


@pytest.fixture
def magic_link(user):

    def _create(request):
        return create_magiclink(user.email, request, redirect_url='')

    return _create
