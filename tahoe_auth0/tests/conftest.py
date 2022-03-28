"""
Pytest helpers.
"""

import pytest

import tahoe_auth0.helpers


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
