"""A mock for openedx site_configuration.helpers"""


configurations = {"ENABLE_TAHOE_AUTH0": True}


def get_value(value, default=None):
    return configurations.get(value, default)
