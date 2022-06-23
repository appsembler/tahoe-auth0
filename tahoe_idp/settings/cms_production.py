"""
CMS/Studio settings.
"""

from .common_production import magiclink_settings


def plugin_settings(settings):
    magiclink_settings(settings)

    # MagicLinkBackend should be the first used backend
    magiclink_backend = 'tahoe_idp.magiclink_backends.MagicLinkBackend'
    if magiclink_backend not in settings.AUTHENTICATION_BACKENDS:
        settings.AUTHENTICATION_BACKENDS.insert(0, magiclink_backend)
