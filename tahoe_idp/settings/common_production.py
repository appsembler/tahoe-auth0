"""
Common production settings.
"""

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
    MAGICLINK_STUDIO_PERMISSION_METHOD: path of the method to be used to check if the user is permitted to use
        magic-links to studio or not. The path must be in the form: "module.submodule:method". It should also be in
        the form: def method(user)
    """
    settings.MAGICLINK_LOGIN_FAILED_REDIRECT = getattr(settings, 'MAGICLINK_LOGIN_FAILED_REDIRECT', '')

    minimum_token_length = 20
    default_token_length = 50

    try:
        token_length = int(getattr(settings, 'MAGICLINK_TOKEN_LENGTH', default_token_length))
    except ValueError:
        raise ImproperlyConfigured('"MAGICLINK_TOKEN_LENGTH" must be an integer')

    settings.MAGICLINK_TOKEN_LENGTH = max(token_length, minimum_token_length)

    try:
        # In seconds
        settings.MAGICLINK_AUTH_TIMEOUT = int(getattr(settings, 'MAGICLINK_AUTH_TIMEOUT', 300))
    except ValueError:
        raise ImproperlyConfigured('"MAGICLINK_AUTH_TIMEOUT" must be an integer')

    try:
        settings.MAGICLINK_LOGIN_REQUEST_TIME_LIMIT = int(getattr(settings, 'MAGICLINK_LOGIN_REQUEST_TIME_LIMIT', 30))
    except ValueError:
        raise ImproperlyConfigured('"MAGICLINK_LOGIN_REQUEST_TIME_LIMIT" must be an integer')

    settings.MAGICLINK_LOGIN_VERIFY_URL = getattr(settings, 'MAGICLINK_LOGIN_VERIFY_URL', 'tahoe_idp:verify_login')

    settings.MAGICLINK_STUDIO_DOMAIN = getattr(settings, 'MAGICLINK_STUDIO_DOMAIN', 'studio.example.com')

    settings.MAGICLINK_STUDIO_PERMISSION_METHOD = getattr(settings, 'MAGICLINK_STUDIO_PERMISSION_METHOD', None)
