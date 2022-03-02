import logging
import urllib.parse

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers

logger = logging.getLogger(__name__)


def is_auth0_enabled():
    """
    A helper method that checks if Auth0 is enabled or not.

    We will read the feature flag from:
        - Site Configurations
        - settings.FEATURES
    A site configuration is has the highest order, if the flag is not defined
    in the site configurations, we will fallback to settings.FEATURES
    configuration.

    Raises `ImproperlyConfigured` if the configuration not correct.
    """

    is_flag_enabled = configuration_helpers.get_value("ENABLE_TAHOE_AUTH0")

    if is_flag_enabled is None:
        is_flag_enabled = settings.FEATURES.get("ENABLE_TAHOE_AUTH0", False)
        logger.debug(
            "Tahoe Auth0 flag read from settings.FEATURES: {}".format(is_flag_enabled)
        )
    else:
        logger.debug(
            "Tahoe Auth0 flag read from site configuration: {}".format(is_flag_enabled)
        )

    if not isinstance(is_flag_enabled, bool):
        raise ImproperlyConfigured("`ENABLE_TAHOE_AUTH0` must be of boolean type")

    # This can be done in a single line, but I left like this for readability
    if is_flag_enabled:
        auth0_settings = getattr(settings, "TAHOE_AUTH0_CONFIGS", None)

        if not auth0_settings:
            raise ImproperlyConfigured(
                "`TAHOE_AUTH0_CONFIGS` settings must be defined when enabling "
                "Tahoe Auth0"
            )

    return is_flag_enabled


def fail_if_auth0_not_enabled():
    """
    A helper that makes sure Auth0 is enabled or throw an EnvironmentError.
    """
    if not is_auth0_enabled():
        raise EnvironmentError("Tahoe Auth0 is not enabled in your project")


def get_auth0_domain():
    """
    A property method used to fetch auth0 domain from Django's settings.FEATURES
    variable.

    We will raise an ImproperlyConfigured error if we couldn't find the setting.
    """
    fail_if_auth0_not_enabled()
    domain = settings.TAHOE_AUTH0_CONFIGS.get("DOMAIN")

    if not domain:
        raise ImproperlyConfigured("Auth0 `DOMAIN` cannot be empty")

    return domain


def get_client_info():
    """
    A helper method responsible for fetching the access token and the client secret
    from Django settings.FEATURES.
    If either value does not exist, we will raise an ImproperlyConfigured error.
    """
    fail_if_auth0_not_enabled()
    client_id = settings.TAHOE_AUTH0_CONFIGS.get("API_CLIENT_ID")
    client_secret = settings.TAHOE_AUTH0_CONFIGS.get("API_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise ImproperlyConfigured(
            "Both `API_CLIENT_ID` and `API_CLIENT_SECRET` must be present "
            "in your `TAHOE_AUTH0_CONFIGS`"
        )

    return client_id, client_secret


def build_auth0_query(**kwargs):
    """
    Responsible for building a querystring used in Auth0 GET APIs.
    """
    args = [
        urllib.parse.quote_plus('{}:"{}"'.format(key, value))
        for key, value in kwargs.items()
    ]
    return "&".join(args)
