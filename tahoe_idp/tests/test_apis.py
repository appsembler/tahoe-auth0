"""
Tests for the external `api` helpers module.
"""
import uuid
from unittest.mock import patch, Mock

import pytest
from django.contrib.auth.models import AnonymousUser, User
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.test.client import RequestFactory
from requests import HTTPError
from social_django.models import UserSocialAuth
from tahoe_idp.api import (
    get_studio_site,
    get_studio_site_configuration,
    get_tahoe_idp_id_by_user,
    request_password_reset,
    save_studio_site_uuid_in_session,
    TahoeIdpStudioException,
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


def studio_request_factory(studio_site_uuid=None):
    if studio_site_uuid is None:
        studio_site_uuid = str(uuid.uuid4())

    request = RequestFactory().get('dummy.com', {'studio_site_uuid': studio_site_uuid})
    request.session = {}
    return request


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
        'https://domain.world/dbconnections/change_password',
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
        'https://domain.world/dbconnections/change_password',
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
    requests_mock.patch(
        'https://domain.world/api/v2/users/auth0|8d8be3c5f86c1a3e',
        headers={
            'content-type': 'application/json',
        },
        text='success',
    )
    user, _social = user_with_social_factory(social_uid='auth0|8d8be3c5f86c1a3e')
    response = update_user(user, {
        'email': 'new_email@example.local',
    })
    assert response.status_code == 200, 'should succeed: {}'.format(response.content.decode('utf-8'))


@mock_tahoe_idp_api_settings
def test_failed_update_user_helper(requests_mock):
    """
    Ensure an error is raised if something goes wrong with `update_user`.
    """
    requests_mock.patch(
        'https://domain.world/api/v2/users/auth0|a4f92ba3f42435cd',
        headers={
            'content-type': 'application/json',
        },
        status_code=400,  # Simulate an error
        text='Connection does not exist',
    )
    user, _social = user_with_social_factory(social_uid='auth0|a4f92ba3f42435cd')
    with pytest.raises(HTTPError, match='400 Client Error'):
        update_user(user, properties={
            'name': 'new name',
        })


@patch('tahoe_idp.api.update_user')
def test_update_user_email(mock_update_user):
    """
    Test `update_user_email`.
    """
    assert not mock_update_user.called
    user, _social = user_with_social_factory(social_uid='auth0|8d8be3c5f86c1a3e')
    update_user_email(user, 'test.email@example.com')
    mock_update_user.assert_called_once_with(user, properties={'email': 'test.email@example.com'})


@patch('tahoe_idp.api.update_user')
def test_update_user_email_verified(mock_update_user):
    """
    Test `update_user_email` with verified.
    """
    assert not mock_update_user.called
    user, _social = user_with_social_factory(social_uid='auth0|8d8be3c5f86c1a3e')
    update_user_email(user, 'test.email@example.com', set_email_as_verified=True)
    mock_update_user.assert_called_once_with(user, properties={
        'email': 'test.email@example.com',
        'email_verified': True,
    })


def test_get_studio_site_no_session():
    """
    Verify that get_studio_site raises TahoeIdpMissingStudioException when session or studio_site_uuid is missing
    """
    request = studio_request_factory()
    error_msg = 'get_studio_site did not find a session in the request!'

    with patch('tahoe_idp.api.crum.get_current_request', return_value=request):
        request.session = None
        with pytest.raises(TahoeIdpStudioException, match=error_msg):
            get_studio_site()

        del request.session
        with pytest.raises(TahoeIdpStudioException, match=error_msg):
            get_studio_site()


def test_get_studio_site_no_uuid():
    """
    Verify that get_studio_site raises TahoeIdpMissingStudioException when session or studio_site_uuid is missing
    """
    request = studio_request_factory()
    error_msg = 'get_studio_site did not find studio_site_uuid in the session!'

    with patch('tahoe_idp.api.crum.get_current_request', return_value=request):
        with pytest.raises(TahoeIdpStudioException, match=error_msg):
            get_studio_site()

        request.session['studio_site_uuid'] = None
        with pytest.raises(TahoeIdpStudioException, match=error_msg):
            get_studio_site()


@patch('tahoe_idp.api.crum.get_current_request', Mock(return_value=Mock(session={'studio_site_uuid': 'dummy_uuid'})))
@patch('tahoe_idp.api.get_site_by_uuid', Mock(return_value=Mock(check_id=99)))
def test_get_studio_site_success():
    """
    Verify that get_studio_site returns the correct site
    """
    assert get_studio_site().check_id == 99


@pytest.mark.parametrize('current_site', [Mock({}), Mock(configuration=None)])
def test_get_studio_site_configuration_no_or_none_configuration(current_site):
    """
    Verify that get_studio_site_configuration raises TahoeIdpMissingStudioException when the current studio
    site does not have a configuration
    """
    with patch('tahoe_idp.api.get_studio_site', return_value=current_site):
        with pytest.raises(
            TahoeIdpStudioException,
            match='get_studio_site_configuration did not a valid site configuration!'
        ):
            get_studio_site_configuration()


@patch('tahoe_idp.api.get_studio_site', Mock(return_value=Mock(configuration=Mock(check_id=99))))
def test_get_studio_site_configuration_success():
    """
    Verify that get_studio_site_configuration returns the correct site configuration
    """
    assert get_studio_site_configuration().check_id == 99


def test_save_studio_site_uuid_in_session_no_session():
    """
    Verify that save_studio_site_uuid_in_session returns None if the session is missing
    """
    request = studio_request_factory()

    request.session = None
    with patch('tahoe_idp.api.crum.get_current_request', return_value=request):
        assert save_studio_site_uuid_in_session(studio_site_uuid='any uuid') is None

    del request.session
    with patch('tahoe_idp.api.crum.get_current_request', return_value=request):
        assert save_studio_site_uuid_in_session(studio_site_uuid='any uuid') is None
    assert not hasattr(request, 'session')


def test_save_studio_site_uuid_in_session_invalid_uuid():
    """
    Verify that save_studio_site_uuid_in_session returns None if the session is missing
    """
    request = studio_request_factory()

    with patch('tahoe_idp.api.crum.get_current_request', return_value=request):
        with pytest.raises(ValueError, match=r'Invalid site uuid cannot be saved in session! \(invalid uuid\)'):
            assert save_studio_site_uuid_in_session(studio_site_uuid='invalid uuid') is None


def test_save_studio_site_uuid_in_session_success():
    """
    Verify that save_studio_site_uuid_in_session saves studio_site_uuid value in session correctly
    """
    studio_site_uuid = str(uuid.uuid4())
    request = studio_request_factory(studio_site_uuid)

    with patch('tahoe_idp.api.crum.get_current_request', return_value=request):
        with patch('tahoe_idp.api.get_site_by_uuid'):
            assert save_studio_site_uuid_in_session(studio_site_uuid=studio_site_uuid) == studio_site_uuid

    assert request.session['studio_site_uuid'] == studio_site_uuid
