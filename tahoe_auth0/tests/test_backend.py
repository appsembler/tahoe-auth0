from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings
from social_core.tests.backends.oauth import OAuth2Test

TEST_FEATURES = {
    "AUTH0_DOMAIN": "example.com",
    "ENABLE_THIRD_PARTY_AUTH": True,
}


class TestAuth0(OAuth2Test):
    backend_path = "tahoe_auth0.auth0backend.Auth0"

    def set_social_auth_setting(self, setting_name, value):
        """
        Set a social auth django setting during the middle of a test.
        """
        # The inherited backend defines self.name, i.e. "tahoe-auth0".
        backend_name = self.name

        # NOTE: We use the strategy's method, rather than override_settings, because
        # the TestStrategy class being used does not rely on Django settings.
        settings = "SOCIAL_AUTH_{}_{}".format(backend_name, setting_name)
        self.strategy.set_settings({settings: value})

    @override_settings(FEATURES=TEST_FEATURES)
    def test_auth0_domain_correct(self):
        self.assertEqual(self.backend.auth0_domain, TEST_FEATURES["AUTH0_DOMAIN"])

    @override_settings(FEATURES={})
    def test_auth0_domain_not_set(self):
        with self.assertRaises(ImproperlyConfigured):
            _ = self.backend.auth0_domain
