import logging
import urllib.parse

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


from site_config_client.openedx import api as config_client_api

logger = logging.getLogger(__name__)


def is_tahoe_idp_enabled():
    """
    A helper method that checks if Tahoe IdP is enabled or not.

    We will read the feature flag from:
        - Site Configurations
        - settings.FEATURES
    A site configuration is has the highest order, if the flag is not defined
    in the site configurations, we will fallback to settings.FEATURES
    configuration.

    Raises `ImproperlyConfigured` if the configuration not correct.
    """

    is_flag_enabled = config_client_api.get_admin_value("ENABLE_TAHOE_IDP")

    if is_flag_enabled is None:
        is_flag_enabled = settings.FEATURES.get("ENABLE_TAHOE_IDP", False)
        logger.debug(
            "Tahoe IdP flag read from settings.FEATURES: {}".format(is_flag_enabled)
        )
    else:
        logger.debug(
            "Tahoe IdP flag read from site configuration: {}".format(is_flag_enabled)
        )

    if not isinstance(is_flag_enabled, bool):
        raise ImproperlyConfigured("`ENABLE_TAHOE_IDP` must be of boolean type")

    # This can be done in a single line, but I left like this for readability
    if is_flag_enabled:
        tahoe_idp_settings = getattr(settings, "TAHOE_IDP_CONFIGS", None)

        if not tahoe_idp_settings:
            raise ImproperlyConfigured(
                "`TAHOE_IDP_CONFIGS` settings must be defined when enabling "
                "Tahoe IdP"
            )

    return is_flag_enabled


def fail_if_tahoe_idp_not_enabled():
    """
    A helper that makes sure Tahoe IdP is enabled or throw an EnvironmentError.
    """
    if not is_tahoe_idp_enabled():
        raise EnvironmentError("Tahoe IdP is not enabled in your project")


def get_idp_domain():
    """
    A property method used to fetch IdP domain from Django's settings variable.

    We will raise an ImproperlyConfigured error if we couldn't find the setting.
    """
    fail_if_tahoe_idp_not_enabled()
    domain = settings.TAHOE_IDP_CONFIGS.get("DOMAIN")

    if not domain:
        raise ImproperlyConfigured("Tahoe IdP `DOMAIN` cannot be empty")

    return domain


def get_client_info():
    """
    A helper method responsible for fetching the access token and the client secret
    from Django settings.FEATURES.
    If either value does not exist, we will raise an ImproperlyConfigured error.
    """
    fail_if_tahoe_idp_not_enabled()
    client_id = settings.TAHOE_IDP_CONFIGS.get("API_CLIENT_ID")
    client_secret = settings.TAHOE_IDP_CONFIGS.get("API_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise ImproperlyConfigured(
            "Both `API_CLIENT_ID` and `API_CLIENT_SECRET` must be present "
            "in your `TAHOE_IDP_CONFIGS`"
        )

    return client_id, client_secret


def build_auth0_query(**kwargs):
    """
    Responsible for building a querystring used in Tahoe IdP GET APIs.

    This is Auth0-specific.
    """
    args = [
        urllib.parse.quote_plus('{}:"{}"'.format(key, value))
        for key, value in kwargs.items()
    ]
    return "&".join(args)
