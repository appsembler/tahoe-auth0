"""
Pytest helpers.
"""

import pytest

from site_config_client.openedx.test_helpers import override_site_config

import tahoe_idp.helpers

MOCK_TENANT_ID = '479d8c4e-d441-11ec-8ebb-6f8318ddff9a'
MOCK_CLIENT_ID = 'a-key'
MOCK_CLIENT_SECRET = 'a-secret-key'
MOCK_DEFAULT_IDP_HINT = '6f60f5bb-82e5-41a1-911d-7a4cd94810f5'


@pytest.fixture(scope='function')
def mock_tahoe_idp_settings(monkeypatch, settings):
    """
    Mock configs to enable Tahoe IdP and set TAHOE_IDP_CONFIGS.
    """
    def mock_is_tahoe_idp_enabled():
        """Mock for `is_tahoe_idp_enabled` to return always True."""
        return True

    settings.TAHOE_IDP_CONFIGS = {
        'BASE_URL': 'https://domain',
        'API_KEY': 'dummy-client-secret',
    }

    monkeypatch.setattr(tahoe_idp.helpers, 'is_tahoe_idp_enabled', mock_is_tahoe_idp_enabled)


def mock_tahoe_idp_api_settings(test_func, add_idp_hint=False):
    """
    Mock API related configuration and settings to make API calls easier in tests.
    """
    extra_params = {'DEFAULT_IDP_HINT': MOCK_DEFAULT_IDP_HINT} if add_idp_hint else {}
    admin_patch = override_site_config(
        config_type='admin',
        TAHOE_IDP_TENANT_ID=MOCK_TENANT_ID,
        TAHOE_IDP_CLIENT_ID=MOCK_CLIENT_ID,
        **extra_params,
    )
    secret_patch = override_site_config(
        config_type='secret',
        TAHOE_IDP_CLIENT_SECRET=MOCK_CLIENT_SECRET,
    )
    return secret_patch(admin_patch(test_func))


def mock_tahoe_idp_api_settings_with_idp_hint(test_func):
    return mock_tahoe_idp_api_settings(test_func=test_func, add_idp_hint=True)
