"""
Pytest helpers.
"""

import pytest
from unittest.mock import patch, Mock

from site_config_client.openedx.test_helpers import override_site_config

import tahoe_auth0.helpers
from tahoe_auth0.api_client import Auth0ApiClient


@pytest.fixture(scope='function')
def mock_auth0_settings(monkeypatch, settings):
    """
    Mock configs to enable auth0 and set TAHOE_AUTH0_CONFIGS.
    """
    def mock_is_auth0_enabled():
        """Mock for `is_auth0_enabled` to return always True."""
        return True

    settings.TAHOE_AUTH0_CONFIGS = {
        'DOMAIN': 'domain.world',
        'API_CLIENT_ID': 'dummy-client-id',
        'API_CLIENT_SECRET': 'dummy-client-secret',
    }

    monkeypatch.setattr(tahoe_auth0.helpers, 'is_auth0_enabled', mock_is_auth0_enabled)


def mock_auth0_api_settings(test_func):
    """
    Mock API related configuration and settings to make API calls easier in tests.
    """
    admin_patch = override_site_config(
        config_type='admin',
        AUTH0_ORGANIZATION_ID='org_testxyz',
        AUTH0_CONNECTION_ID='con-testxyz',
    )
    access_token_patch = patch.object(Auth0ApiClient, '_get_access_token', Mock(return_value='xyz-token'))
    return access_token_patch(admin_patch(test_func))
