import pytest
from unittest.mock import patch

from ddt import data, ddt, unpack
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings

from site_config_client.openedx.test_helpers import override_site_config

from tahoe_idp.helpers import (
    fail_if_tahoe_idp_not_enabled,
    fusionauth_retrieve_user,
    get_idp_base_url,
    get_required_setting,
    get_tenant_id,
    is_tahoe_idp_enabled,
    is_valid_redirect_url,
)


class TestBaseURL(TestCase):
    @override_settings(TAHOE_IDP_CONFIGS={})
    @override_site_config("admin", ENABLE_TAHOE_IDP=True)
    def test_no_base_url(self):
        with self.assertRaises(ImproperlyConfigured):
            get_idp_base_url()

    @override_settings(TAHOE_IDP_CONFIGS={"BASE_URL": "http://fa:9100"})
    @override_site_config("admin", ENABLE_TAHOE_IDP=True)
    def test_with_base_url(self):
        base_url = get_idp_base_url()
        self.assertEqual(base_url, "http://fa:9100")


@override_settings(TAHOE_IDP_CONFIGS={"BASE_URL": "http://fa:9100"})
@override_site_config("admin", ENABLE_TAHOE_IDP=True)
def test_required_setting_not_available():
    with pytest.raises(ImproperlyConfigured, match='`API_KEY` cannot be empty'):
        get_required_setting("API_KEY")


@override_settings(TAHOE_IDP_CONFIGS={"BASE_URL": "http://fa:9100"})
@override_site_config("admin", ENABLE_TAHOE_IDP=True)
def test_missing_required_tenant_id():
    with pytest.raises(ImproperlyConfigured, match='`TAHOE_IDP_TENANT_ID` cannot be empty'):
        get_tenant_id()


@override_settings(TAHOE_IDP_CONFIGS={"BASE_URL": "http://fa:9100", "API_KEY": "testkey"})
@override_site_config("admin", ENABLE_TAHOE_IDP=True, TAHOE_IDP_TENANT_ID="tenant-xyz")
def test_fusionauth_retrieve_user(requests_mock):
    requests_mock.get(
        "/api/user/855760ec-d5bc-11ec-9f0a-c3fd7676521c",
        headers={
            'content-type': 'application/json',
        },
        status_code=200,
        json={
            "user": {
                "id": "855760ec-d5bc-11ec-9f0a-c3fd7676521c",
                "username": "ahmedjazzar",
            },
        },
    )
    user = fusionauth_retrieve_user("855760ec-d5bc-11ec-9f0a-c3fd7676521c")
    assert user == {
        "id": "855760ec-d5bc-11ec-9f0a-c3fd7676521c",
        "username": "ahmedjazzar",
    }


@ddt
class TestIsTahoeIdPEnabled(TestCase):
    @unpack
    @data(
        {"configuration_flag": None, "feature_flag": True, "is_enabled": True},
        {"configuration_flag": None, "feature_flag": False, "is_enabled": False},
        {"configuration_flag": True, "feature_flag": True, "is_enabled": True},
        {"configuration_flag": True, "feature_flag": False, "is_enabled": True},
        {"configuration_flag": False, "feature_flag": True, "is_enabled": False},
        {"configuration_flag": False, "feature_flag": False, "is_enabled": False},
    )
    def test_flag_and_configurations_priorities(
        self, configuration_flag, feature_flag, is_enabled
    ):
        """
        A site configuration is of higher order, if nothing is defined in the
        site configurations, we will fallback to settings.FEATURES configuration
        """
        with override_settings(FEATURES={"ENABLE_TAHOE_IDP": feature_flag}):
            with override_site_config("admin", ENABLE_TAHOE_IDP=configuration_flag):
                self.assertEqual(is_enabled, is_tahoe_idp_enabled())

    @override_settings(TAHOE_IDP_CONFIGS={})
    @override_site_config("admin", ENABLE_TAHOE_IDP=True)
    def test_flag_enabled_no_settings(self):
        message = (
            "`TAHOE_IDP_CONFIGS` settings must be defined when enabling Tahoe IdP"
        )
        with self.assertRaisesMessage(ImproperlyConfigured, message):
            is_tahoe_idp_enabled()

    @override_settings(TAHOE_IDP_CONFIGS=None)
    @override_site_config("admin", ENABLE_TAHOE_IDP=True)
    def test_flag_enabled_none_settings(self):
        message = (
            "`TAHOE_IDP_CONFIGS` settings must be defined when enabling Tahoe IdP"
        )
        with self.assertRaisesMessage(ImproperlyConfigured, message):
            is_tahoe_idp_enabled()

    @override_site_config("admin", ENABLE_TAHOE_IDP="True")
    def test_idp_settings_enabled_not_boolean(self):
        message = "`ENABLE_TAHOE_IDP` must be of boolean type"
        with self.assertRaisesMessage(ImproperlyConfigured, message):
            is_tahoe_idp_enabled()

    @override_settings(
        TAHOE_IDP_CONFIGS={
            "DOMAIN": "test.com",
            "API_CLIENT_ID": "client-id",
            "API_CLIENT_SECRET": "client-secret",
        },
    )
    @override_site_config("admin", ENABLE_TAHOE_IDP=True)
    def test_tahoe_idp_enabled(self):
        self.assertEqual(True, is_tahoe_idp_enabled())


class TestTahoeIdPEnabledHelper(TestCase):
    @patch("tahoe_idp.helpers.is_tahoe_idp_enabled", return_value=False)
    def test_not_enabled(self, mock_is_tahoe_idp_enabled):
        with self.assertRaises(EnvironmentError):
            fail_if_tahoe_idp_not_enabled()

        mock_is_tahoe_idp_enabled.assert_called_once_with()

    @patch("tahoe_idp.helpers.is_tahoe_idp_enabled", return_value=True)
    def test_enabled(self, mock_is_tahoe_idp_enabled):
        fail_if_tahoe_idp_not_enabled()
        mock_is_tahoe_idp_enabled.assert_called_once_with()


@ddt
class TestIsValidRedirectURL(TestCase):
    """
    Tests for is_valid_redirect_url helper
    """

    def test_default_white_list(self):
        """
        Guard test to verify that LOGIN_REDIRECT_WHITELIST is empty for all tests. If a test needs it to be filled,
        it will mock it (override it) internally
        """
        assert getattr(settings, 'LOGIN_REDIRECT_WHITELIST', []) == []

    @data(
        ('home', 'example.com'),
        ('home', 'subdomain.example.com'),
        ('home', 'https://example.com'),
        ('https://example.com', 'example.com'),
        ('https://example.com/someurl', 'example.com'),
        ('https://subdomain.example.com/someurl', 'subdomain.example.com'),
    )
    @unpack
    def test_valid_by_comparing_to_host(self, redirect_to, request_host):
        """
        Verify that is_valid_redirect_url returns True if redirect_to host is the same as request_host
        """
        assert is_valid_redirect_url(redirect_to, request_host, False)

    @data(
        ('https://subdomain.example.com/someurl', 'example.com'),
        ('https://otherexample.com', 'example.com'),
    )
    @unpack
    def test_not_valid_by_comparing_to_host(self, redirect_to, request_host):
        """
        Verify that is_valid_redirect_url returns False if redirect_to host is anything not equal to request_host
        """
        assert not is_valid_redirect_url(redirect_to, request_host, False)

    @data(
        ('home', 'example.com'),
        ('home', 'subdomain.example.com'),
        ('home', 'https://example.com'),
        ('home', 'http://example.com'),
        ('https://example.com', 'example.com'),
    )
    @unpack
    def test_valid_by_require_https(self, redirect_to, request_host):
        """
        When require_https is set. Verify that is_valid_redirect_url returns True if both
        redirect_to and request_host are using https
        """
        assert is_valid_redirect_url(redirect_to, request_host, True)

    @data(
        ('http://example.com', 'example.com'),
        ('http://example.com', 'http://example.com'),
        ('https://example.com', 'http://example.com'),
        ('http://example.com', 'https://example.com'),
    )
    @unpack
    def test_not_valid_by_require_https(self, redirect_to, request_host):
        """
        When require_https is set. Verify that is_valid_redirect_url returns False if redirect_to or request_host
        are not using https
        """
        assert not is_valid_redirect_url(redirect_to, request_host, True)

    @data(
        ('https://subdomain.example.com/someurl', 'example.com'),
        ('https://otherexample.com', 'example.com'),
    )
    @unpack
    def test_valid_by_comparing_to_whitelist(self, redirect_to, request_host):
        """
        Verify that is_valid_redirect_url returns True if redirect_to host is in LOGIN_REDIRECT_WHITELIST
        """
        assert not is_valid_redirect_url(redirect_to, request_host, True)

        with override_settings(LOGIN_REDIRECT_WHITELIST=['subdomain.example.com', 'otherexample.com']):
            assert is_valid_redirect_url(redirect_to, request_host, True)
