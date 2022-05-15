from unittest.mock import patch

from ddt import data, ddt, unpack
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings

from site_config_client.openedx.test_helpers import override_site_config

from tahoe_idp.helpers import (
    fail_if_tahoe_idp_not_enabled,
    get_idp_base_url,
    is_tahoe_idp_enabled,
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


@ddt
class TestIsAuth0Enabled(TestCase):
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
    def test_auth0_settings_enabled_not_boolean(self):
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
    def test_auth0_enabled(self):
        self.assertEqual(True, is_tahoe_idp_enabled())


class TestAuth0EnabledDecorator(TestCase):
    @patch("tahoe_idp.helpers.is_tahoe_idp_enabled", return_value=False)
    def test_not_enabled(self, mock_is_tahoe_idp_enabled):
        with self.assertRaises(EnvironmentError):
            fail_if_tahoe_idp_not_enabled()

        mock_is_tahoe_idp_enabled.assert_called_once_with()

    @patch("tahoe_idp.helpers.is_tahoe_idp_enabled", return_value=True)
    def test_enabled(self, mock_is_tahoe_idp_enabled):
        fail_if_tahoe_idp_not_enabled()
        mock_is_tahoe_idp_enabled.assert_called_once_with()
