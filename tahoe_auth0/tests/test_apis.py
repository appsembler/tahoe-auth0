"""
Tests for the external `api` helpers module.
"""
import pytest
from requests import HTTPError
from unittest.mock import patch, Mock, PropertyMock

from django.conf import settings

from tahoe_auth0.api_client import Auth0ApiClient
from tahoe_auth0.api import (
    request_password_reset,
)


@patch.dict(settings.TAHOE_AUTH0_CONFIGS, {
    'DOMAIN': 'example.auth0.local',
    'API_CLIENT_ID': 'dummy-client-id',
    'API_CLIENT_SECRET': 'dummy-client-secret',
})
@patch.object(Auth0ApiClient, 'organization_id', PropertyMock(return_value='org_xyz'))
@patch.object(Auth0ApiClient, "_get_access_token", Mock(return_value='xyz-token'))
def test_password_reset_helper(requests_mock):
    """
    Password reset can be requested.
    """
    requests_mock.post(
        'https://example.auth0.local/dbconnections/change_password',
        headers={
            'content-type': 'application/json',
        },
        text='success',
    )
    response = request_password_reset('someone@example.com')
    assert response.status_code == 200, 'should succeed: {}'.format(response.content.decode('utf-8'))


@patch.dict(settings.TAHOE_AUTH0_CONFIGS, {
    'DOMAIN': 'example.auth0.local',
    'API_CLIENT_ID': 'dummy-client-id',
    'API_CLIENT_SECRET': 'dummy-client-secret',
})
@patch.object(Auth0ApiClient, 'organization_id', PropertyMock(return_value='org_xyz'))
@patch.object(Auth0ApiClient, "_get_access_token", Mock(return_value='xyz-token'))
def test_password_reset_helper_unauthorized(requests_mock):
    """
    Ensure an error is raised if something goes wrong.
    """
    requests_mock.post(
        'https://example.auth0.local/dbconnections/change_password',
        headers={
            'content-type': 'application/json',
        },
        status_code=501,  # Simulate an error
        text='success',
    )
    with pytest.raises(HTTPError, match='501 Server Error'):
        request_password_reset('someone@example.com')
