import pytest
from django.contrib.auth import get_user_model

from tahoe_idp.magiclink_helpers import create_magiclink

User = get_user_model()


@pytest.fixture()
def user():
    the_user = User.objects.create(
        email='test@example.com',
        username='test_user'
    )
    the_user.set_password('password')
    the_user.save()
    return the_user


@pytest.fixture
def magic_link(user):

    def _create(request):
        return create_magiclink(user.username, request, redirect_url='')

    return _create


def external_method_testing(user):
    """
    used to test the functionality of is_studio_allowed_for_user helper
    """
    return user.email == 'permitted@example.com'
