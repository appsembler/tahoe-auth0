"""A mock for openedx get_current_organization"""

from django.conf import settings


class Organization(object):
    name = "{} Academy".format(settings.GET_CURRENT_ORGANIZATION_MOCK)
    short_name = settings.GET_CURRENT_ORGANIZATION_MOCK


def get_current_organization():
    return Organization()
