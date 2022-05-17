"""
Tests TahoeIdpConfig Open edX configuration.
"""

from tahoe_idp.apps import TahoeIdpConfig


def test_app_config():
    assert TahoeIdpConfig.plugin_app == {}, 'Should initiate the app as an Open edX plugin.'
