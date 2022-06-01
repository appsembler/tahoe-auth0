# fdddlake8: nodddqa: E501
import warnings
from django.core.exceptions import ImproperlyConfigured


def magiclink_settings(settings):
    settings.LOGIN_FAILED_REDIRECT = getattr(settings, 'MAGICLINK_LOGIN_FAILED_REDIRECT', '')

    try:
        settings.TOKEN_LENGTH = int(getattr(settings, 'MAGICLINK_TOKEN_LENGTH', 50))
    except ValueError:
        raise ImproperlyConfigured('"MAGICLINK_TOKEN_LENGTH" must be an integer')
    else:
        if settings.TOKEN_LENGTH < 20:
            warning = ('Shorter MAGICLINK_TOKEN_LENGTH values make your login more'
                       'sussptable to brute force attacks')
            warnings.warn(warning, RuntimeWarning)

    try:
        # In seconds
        settings.AUTH_TIMEOUT = int(getattr(settings, 'MAGICLINK_AUTH_TIMEOUT', 300))
    except ValueError:
        raise ImproperlyConfigured('"MAGICLINK_AUTH_TIMEOUT" must be an integer')

    try:
        # Time limit in seconds
        settings.LOGIN_REQUEST_TIME_LIMIT = int(getattr(settings, 'MAGICLINK_LOGIN_REQUEST_TIME_LIMIT', 30))
    except ValueError:
        raise ImproperlyConfigured('"MAGICLINK_LOGIN_REQUEST_TIME_LIMIT" must be an integer')

    settings.LOGIN_VERIFY_URL = getattr(settings, 'MAGICLINK_LOGIN_VERIFY_URL', 'tahoe_idp:login_verify')

    settings.STUDIO_DOMAIN = getattr(settings, 'MAGICLINK_STUDIO_DOMAIN', 'studio.example.com')

    settings.AUTHENTICATION_BACKENDS.insert(0, 'tahoe_idp.magiclink_backends.MagicLinkBackend')


def plugin_settings(settings):
    magiclink_settings(settings)
