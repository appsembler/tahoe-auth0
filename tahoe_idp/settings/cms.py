from . import common


def plugin_settings(settings):
    common.plugin_settings(settings)
    settings.AUTHENTICATION_BACKENDS = [
        'magiclink.backends.MagicLinkBackend'
    ] + settings.AUTHENTICATION_BACKENDS

    settings.MAGICLINK_REQUIRE_SIGNUP = True
    settings.MAGICLINK_LOGIN_FAILED_REDIRECT = '/'  # TODO: Make a better page
    settings.LOGIN_REDIRECT_URL = '/home'

    settings.MAGICLINK_ALLOW_SUPERUSER_LOGIN = False
    settings.MAGICLINK_ALLOW_STAFF_LOGIN = False

