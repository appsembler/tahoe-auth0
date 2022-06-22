"""
Tests for the openedx production.py settings.
"""
import pytest
from django.core.exceptions import ImproperlyConfigured

from tahoe_idp.settings.production import plugin_settings


def test_tpa_backend_settings(settings):
    """
    Test settings third party auth backends.
    """
    settings.THIRD_PARTY_AUTH_BACKENDS = ['dummy_backend']
    plugin_settings(settings)

    backend_path = 'tahoe_idp.backend.TahoeIdpOAuth2'
    assert backend_path == settings.THIRD_PARTY_AUTH_BACKENDS[0], 'TahoeIdpOAuth2 goes first'

    plugin_settings(settings)
    assert settings.THIRD_PARTY_AUTH_BACKENDS.count(backend_path) == 1, 'adds only one instance'


def test_authentication_backend_settings(settings):
    """
    Test settings third party auth backends.
    """
    settings.AUTHENTICATION_BACKENDS = ['some_other_backend']
    backend_path = 'tahoe_idp.magiclink_backends.MagicLinkBackend'

    plugin_settings(settings)
    assert backend_path == settings.AUTHENTICATION_BACKENDS[0], 'MagicLinkBackend goes first'

    plugin_settings(settings)
    assert settings.AUTHENTICATION_BACKENDS.count(backend_path) == 1, 'add only one instance'


@pytest.mark.parametrize('invalid_test_case', [
    {
        'name': 'MAGICLINK_TOKEN_LENGTH',
        'value': 'not integer',
        'message': '"MAGICLINK_TOKEN_LENGTH" must be an integer',
    },
    {
        'name': 'MAGICLINK_AUTH_TIMEOUT',
        'value': 'some weird value',
        'message': '"MAGICLINK_AUTH_TIMEOUT" must be an integer',
    },
    {
        'name': 'MAGICLINK_LOGIN_REQUEST_TIME_LIMIT',
        'value': 'not integer',
        'message': '"MAGICLINK_LOGIN_REQUEST_TIME_LIMIT" must be an integer',
    },
])
def test_wrong_settings(settings, invalid_test_case):
    """
    Tests a couple of bad configuration to ensure proper error messages are raised.
    """
    setattr(settings, invalid_test_case['name'], invalid_test_case['value'])

    with pytest.raises(ImproperlyConfigured, match=invalid_test_case['message']):
        plugin_settings(settings)


def test_token_length_configs(settings):
    """
    Ensure MAGICLINK_TOKEN_LENGTH is validated for security.
    """
    plugin_settings(settings)
    assert settings.MAGICLINK_TOKEN_LENGTH == 50, 'default to 50'

    settings.MAGICLINK_TOKEN_LENGTH = 19
    plugin_settings(settings)
    assert settings.MAGICLINK_TOKEN_LENGTH == 20, 'do not allow less than 20'

    settings.MAGICLINK_TOKEN_LENGTH = 60
    plugin_settings(settings)
    assert settings.MAGICLINK_TOKEN_LENGTH == 60, 'allow setting any large value'
