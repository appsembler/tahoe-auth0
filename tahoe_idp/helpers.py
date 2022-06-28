"""
Helpers
"""

from importlib import import_module
import logging

from fusionauth.fusionauth_client import FusionAuthClient
from site_config_client.openedx import api as config_client_api

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils import http


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


def get_required_setting(setting_name):
    """
    Get a required Tahoe Identity Provider setting from TAHOE_IDP_CONFIGS.

    We will raise an ImproperlyConfigured error if we couldn't find the setting.
    """
    fail_if_tahoe_idp_not_enabled()
    setting_value = settings.TAHOE_IDP_CONFIGS.get(setting_name)
    if not setting_value:
        raise ImproperlyConfigured("Tahoe IdP `{}` cannot be empty".format(setting_name))

    return setting_value


def get_successful_fusion_auth_http_response(fa_response):
    """
    Raise exceptions for HTTP errors and log the error messages.

    :param fa_response: ClientResponse (fusionauth)
    :return Response (requests)
    """
    http_response = fa_response.response
    if not fa_response.was_successful():
        logger.warning('Failed fusionauth response status=%s, content=%s',
                       http_response.status_code, http_response.content.decode('utf-8'))

    http_response.raise_for_status()
    return http_response


def get_key_and_secret():
    """
    Return tuple with Consumer Key and Consumer Secret for Tahoe IdP OAuth client.
    """
    fail_if_tahoe_idp_not_enabled()
    key = config_client_api.get_admin_value('TAHOE_IDP_CLIENT_ID')
    secret = config_client_api.get_secret_value('TAHOE_IDP_CLIENT_SECRET')

    if not (key and secret):
        raise ImproperlyConfigured("Tahoe IdP `TAHOE_IDP_CLIENT_ID` and `TAHOE_IDP_CLIENT_SECRET` are required.")

    return {
        "key": key,
        "secret": secret,
    }


def get_idp_base_url():
    """
    Get IdP base_url from Django's settings variable.
    """
    return get_required_setting('BASE_URL')


def get_tenant_id():
    """
    Get API_KEY for the FusionAuth API client.
    """
    fail_if_tahoe_idp_not_enabled()
    TAHOE_IDP_TENANT_ID = config_client_api.get_admin_value("TAHOE_IDP_TENANT_ID")

    if not TAHOE_IDP_TENANT_ID:
        raise ImproperlyConfigured("Tahoe IdP `TAHOE_IDP_TENANT_ID` cannot be empty in `admin` Site Configuration.")

    return TAHOE_IDP_TENANT_ID


def get_api_key():
    """
    Get API_KEY for the FusionAuth API client.
    """
    return get_required_setting("API_KEY")


def get_id_jwt_decode_options():
    """
    Get IdP jwt decode configs from Django's settings variable.
    """
    fail_if_tahoe_idp_not_enabled()
    return settings.TAHOE_IDP_CONFIGS.get("JWT_OPTIONS", {})


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


def fusionauth_retrieve_user(user_uuid):
    idp_user_res = get_api_client().retrieve_user(user_uuid)
    response = get_successful_fusion_auth_http_response(idp_user_res)
    return response.json()["user"]


def is_valid_redirect_url(redirect_to, request_host, require_https):
    """
    Verify that the given URL if valid or not

    :param redirect_to: The URL in question
    :param request_host: Originating hostname of the request. This is always considered an acceptable redirect target.
    :param require_https: Whether HTTPs should be required in the redirect URL.
    :return: <True> if valid. <False> otherwise
    """
    login_redirect_whitelist = set(getattr(settings, 'LOGIN_REDIRECT_WHITELIST', []))
    login_redirect_whitelist.add(request_host)

    is_safe_url = http.is_safe_url(
        redirect_to, allowed_hosts=login_redirect_whitelist, require_https=require_https
    )
    return is_safe_url


def import_from_path(path):
    """
    Import a function or class from a string Python path.

    Copied from Figures

    Note: This helper does _not_ attempt to handle exceptions well. Instead, it throws them as is.
    The rationale is that such exceptions are only fixable at the deployment time and attempting to handle such errors
    would risk hiding the errors and making it more difficult to fix.

    :param path: string path in the format "module.submodule:variable".
    :return object
    """
    module_path, variable_name = path.split(':', 1)
    module = import_module(module_path)
    return getattr(module, variable_name)
