"""
Tests for the external `api` helpers module.
"""
import pytest
from django.contrib.auth.models import AnonymousUser, User
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from requests import HTTPError
from social_django.models import UserSocialAuth
from unittest.mock import patch, call

from tahoe_idp.api import (
    get_tahoe_idp_id_by_user,
    request_password_reset,
    update_user,
    update_user_email,
)
from tahoe_idp.constants import BACKEND_NAME


from .conftest import mock_tahoe_idp_api_settings


pytestmark = pytest.mark.usefixtures(
    'mock_tahoe_idp_settings',
    'transactional_db',
)


def user_factory(username='myusername', email=None, **kwargs):
    """
    Stupid user factory.
    """
    return User.objects.create(
        email=email or '{username}@example.local'.format(
            username=username,
        ),
        username=username,
        **kwargs,
    )


def tahoe_idp_entry_factory(user, social_uid):
    """
    Create Tahoe IdP social entry.
    """
    return UserSocialAuth.objects.create(
        user=user,
        uid=social_uid,
        provider=BACKEND_NAME,
    )


def user_with_social_factory(social_uid, user_kwargs=None):
    """
    Create a user with social auth entry.
    """
    user = user_factory(user_kwargs or {})
    social = tahoe_idp_entry_factory(user, social_uid)
    return user, social


@mock_tahoe_idp_api_settings
def test_password_reset_helper(requests_mock):
    """
    Password reset can be requested.
    """
    requests_mock.post(
        'https://domain/api/user/forgot-password',
        headers={
            'content-type': 'application/json',
        },
        text='success',
    )

    response = request_password_reset('someone@example.com')
    assert response.status_code == 200, 'should succeed: {}'.format(response.content.decode('utf-8'))


@mock_tahoe_idp_api_settings
def test_password_reset_helper_unauthorized(requests_mock):
    """
    Ensure an error is raised if something goes wrong.
    """
    requests_mock.post(
        'https://domain/api/user/forgot-password',
        headers={
            'content-type': 'application/json',
        },
        status_code=501,  # Simulate an error
        text='success',
    )
    with pytest.raises(HTTPError, match='501 Server Error'):
        request_password_reset('someone@example.com')


def test_get_tahoe_idp_id_by_user():
    """
    Tests for `get_tahoe_idp_id_by_user` validation and errors.
    """
    social_id = 'auth0|bd7793e40ca2d0ca'
    user, social = user_with_social_factory(social_uid=social_id)
    assert get_tahoe_idp_id_by_user(user=user) == social_id


def test_get_tahoe_idp_id_by_user_validation():
    """
    Tests for `get_tahoe_idp_id_by_user` validation and errors.
    """
    with pytest.raises(ValueError, match='User should be provided'):
        get_tahoe_idp_id_by_user(user=None)

    with pytest.raises(ValueError, match='Non-anonymous User should be provided'):
        get_tahoe_idp_id_by_user(user=AnonymousUser())

    user_without_auth0_id = user_factory()
    with pytest.raises(ObjectDoesNotExist):  # Should fail for malformed data
        get_tahoe_idp_id_by_user(user=user_without_auth0_id)


def test_get_tahoe_idp_id_by_user_two_auth0_ids():
    """
    Tests for `get_tahoe_idp_id_by_user` fail for malformed data.
    """
    user_with_two_ids = user_factory()
    tahoe_idp_entry_factory(user_with_two_ids, 'test1')
    tahoe_idp_entry_factory(user_with_two_ids, 'test2')
    with pytest.raises(MultipleObjectsReturned):  # Should fail for malformed data
        get_tahoe_idp_id_by_user(user=user_with_two_ids)


@mock_tahoe_idp_api_settings
def test_update_user_helper(requests_mock):
    """
    Can update user.
    """
    user_uuid = 'c80f5080-d50c-11ec-b5e5-5b30b2c6a1d9'
    requests_mock.patch(
        'https://domain/api/user/{user_uuid}'.format(user_uuid=user_uuid),
        headers={
            'content-type': 'application/json',
        },
        text='{"success": True}',
    )
    user, _social = user_with_social_factory(social_uid=user_uuid)
    response = update_user(user, {
        'email': 'new_email@example.local',
    })
    assert response.status_code == 200, 'should succeed: {}'.format(response.content.decode('utf-8'))


@mock_tahoe_idp_api_settings
def test_failed_update_user_helper(requests_mock):
    """
    Ensure an error is raised if something goes wrong with `update_user`.
    """
    user_uuid = 'c80f5080-d50c-11ec-b5e5-5b30b2c6a1d9'
    requests_mock.patch(
        'https://domain/api/user/{user_uuid}'.format(user_uuid=user_uuid),
        headers={
            'content-type': 'application/json',
        },
        status_code=400,  # Simulate an error
        text='{"message": "Connection does not exist"}',
    )
    user, _social = user_with_social_factory(social_uid=user_uuid)
    with pytest.raises(HTTPError, match='400 Client Error'):
        update_user(user, properties={
            'name': 'new name',
        })


@patch('tahoe_idp.api.update_user')
@mock_tahoe_idp_api_settings
def test_update_user_email(mock_update_user):
    """
    Test `update_user_email`.
    """
    assert not mock_update_user.called
    user, _social = user_with_social_factory(social_uid='c80f5080-d50c-11ec-b5e5-5b30b2c6a1d9')
    update_user_email(user, 'test.email@example.com')
    mock_update_user.assert_called_once_with(user, properties={
        'user': {
            'email': 'test.email@example.com',
        },
    })


@patch('tahoe_idp.api.update_user')
def test_update_user_email_verified(mock_update_user):
    """
    Test `update_user_email` with verified.
    """
    assert not mock_update_user.called
    user, _social = user_with_social_factory(social_uid='c80f5080-d50c-11ec-b5e5-5b30b2c6a1d9')
    update_user_email(user, 'test.email@example.com', skip_email_verification=True)
    mock_update_user.assert_called_once_with(user, properties={
        'user': {
            'email': 'test.email@example.com',
        },
        'skipVerification': True,
    })

