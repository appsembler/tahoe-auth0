"""
Helpers
"""

import logging
import urllib.parse

import requests
from fusionauth.fusionauth_client import FusionAuthClient
from jose import jwt
from site_config_client.openedx import api as config_client_api

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


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


def get_idp_base_url():
    """
    A property method used to fetch IdP domain from Django's settings variable.

    We will raise an ImproperlyConfigured error if we couldn't find the setting.
    """
    fail_if_tahoe_idp_not_enabled()
    domain = settings.TAHOE_IDP_CONFIGS.get("BASE_URL")

    if not domain:
        raise ImproperlyConfigured("Tahoe IdP `BASE_URL` cannot be empty")

    return domain


def get_tenant_id():
    """
    Get API_KEY for the FusionAuth API client.
    """
    fail_if_tahoe_idp_not_enabled()
    idp_tenant_id = config_client_api.get_admin_value("IDP_TENANT_ID")

    if not idp_tenant_id:
        raise ImproperlyConfigured("Tahoe IdP `IDP_TENANT_ID` cannot be empty in `admin` Site Configuration.")

    return idp_tenant_id


def get_api_key():
    """
    Get API_KEY for the FusionAuth API client.
    """
    fail_if_tahoe_idp_not_enabled()
    api_key = settings.TAHOE_IDP_CONFIGS.get("API_KEY")

    if not api_key:
        raise ImproperlyConfigured("Tahoe IdP `API_KEY` cannot be empty")

    return api_key


def get_id_jwt_decode_options():
    """
    Get IdP jwt decode configs from Django's settings variable.
    """
    fail_if_tahoe_idp_not_enabled()
    return settings.TAHOE_IDP_CONFIGS.get("JWT_OPTIONS", {})


def get_jwt_algorithms():
    """
    Get

    See: https://fusionauth.io/learn/expert-advice/tokens/anatomy-of-jwt
    """
    fail_if_tahoe_idp_not_enabled()
    return settings.TAHOE_IDP_CONFIGS.get("JWT_ALGORITHMS", [
        "HS256",
        "RS256",
        "RS384",
        "RS512",
        "ES256",
        "ES384",
        "ES512",
    ])


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


def get_api_client():
    """
    Get a configured Rest API client for the Identity Provider.
    """
    client = FusionAuthClient(
        api_key=get_api_key(),
        base_url=get_idp_base_url(),
    )
    client.set_tenant_id(get_tenant_id())
    return client


def get_jwt_payload(client_id, id_token):
    """
    Verifies and returns a JWT token payload from the response. A normal returned
    payload looks like the following:
        {
            'iss': 'https://<tenant>.us.auth0.com/',
            'name': 'Ahmed Jazzar',
            'email_verified': False,
            'picture': 'https://s.gravatar.com/avatar/abcd.png',
            'exp': 1633164125,
            'sub': 'auth0|61578ee61e38d9006859b612',
            'email': 'ahmed@appsembler.com',
            'updated_at': '2021-10-01T22:42:54.841Z',
            'iat': 1633128125,
            'nickname': 'ahmed+w0crpcxx7rirspdang',
            'org_id': 'org_2ud2MmLH8vB35m01',
            'aud': '9TbUCXJ9F3u3Q5jyRpOWuKaybiCk3rEa'
        }
    """
    issuer = "{}/".format(get_idp_base_url())
    audience = client_id
    jwks_response = requests.get("{}/.well-known/jwks.json".format(get_idp_base_url()))
    jwks_response.raise_for_status()
    jwks = jwks_response.json()

    return jwt.decode(
        token=id_token,
        key=jwks,
        algorithms=get_jwt_algorithms(),
        audience=audience,
        issuer=issuer,
        options=get_id_jwt_decode_options(),
    )
