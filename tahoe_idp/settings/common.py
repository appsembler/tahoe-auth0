# fdddlake8: nodddqa: E501
import warnings
from django.core.exceptions import ImproperlyConfigured


def magiclink_settings(settings):
    """
    Set MagicLink specific settings:

    MAGICLINK_LOGIN_FAILED_REDIRECT: where to redirect when the magic-link login fails
    MAGICLINK_TOKEN_LENGTH: number of characters used to create a random token for the user
    MAGICLINK_AUTH_TIMEOUT: seconds for the generated magic-link before it becomes expired
    MAGICLINK_LOGIN_REQUEST_TIME_LIMIT: seconds to pass before allowing to generate a new magic-link for the same user
    MAGICLINK_LOGIN_VERIFY_URL: URL to be used to verify the validity of the magic-link. Keep it on default
        unless a customization is needed for some reason!
    MAGICLINK_STUDIO_DOMAIN: Studio domain to be used by magic-link views
    """
    settings.MAGICLINK_LOGIN_FAILED_REDIRECT = getattr(settings, 'MAGICLINK_LOGIN_FAILED_REDIRECT', '')

    try:
        settings.MAGICLINK_TOKEN_LENGTH = int(getattr(settings, 'MAGICLINK_TOKEN_LENGTH', 50))
    except ValueError:
        raise ImproperlyConfigured('"MAGICLINK_TOKEN_LENGTH" must be an integer')
    else:
        if settings.MAGICLINK_TOKEN_LENGTH < 20:
            warning = (
                'Shorter MAGICLINK_TOKEN_LENGTH values make your login more vulnerable to brute force attacks'
            )
            warnings.warn(warning, RuntimeWarning)

    try:
        # In seconds
        settings.MAGICLINK_AUTH_TIMEOUT = int(getattr(settings, 'MAGICLINK_AUTH_TIMEOUT', 300))
    except ValueError:
        raise ImproperlyConfigured('"MAGICLINK_AUTH_TIMEOUT" must be an integer')

    try:
        settings.MAGICLINK_LOGIN_REQUEST_TIME_LIMIT = int(getattr(settings, 'MAGICLINK_LOGIN_REQUEST_TIME_LIMIT', 30))
    except ValueError:
        raise ImproperlyConfigured('"MAGICLINK_LOGIN_REQUEST_TIME_LIMIT" must be an integer')

    settings.MAGICLINK_LOGIN_VERIFY_URL = getattr(settings, 'MAGICLINK_LOGIN_VERIFY_URL', 'tahoe_idp:login_verify')

    settings.MAGICLINK_STUDIO_DOMAIN = getattr(settings, 'MAGICLINK_STUDIO_DOMAIN', 'studio.example.com')

    # MagicLinkBackend should be the first used backend
    settings.AUTHENTICATION_BACKENDS.insert(0, 'tahoe_idp.magiclink_backends.MagicLinkBackend')


def plugin_settings(settings):
    magiclink_settings(settings)
