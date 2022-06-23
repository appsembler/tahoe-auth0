"""
LMS Settings.
"""

from .common_production import magiclink_settings


def plugin_settings(settings):
    magiclink_settings(settings)

    # Add the Social / ThirdPartyAuth backend
    tahoe_idp_backend = 'tahoe_idp.backend.TahoeIdpOAuth2'
    if tahoe_idp_backend not in settings.THIRD_PARTY_AUTH_BACKENDS:
        settings.THIRD_PARTY_AUTH_BACKENDS.insert(0, tahoe_idp_backend)
