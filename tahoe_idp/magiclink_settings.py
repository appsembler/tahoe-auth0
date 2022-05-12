# flake8: noqa: E501
import warnings

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

LOGIN_FAILED_TEMPLATE_NAME = getattr(
    settings,
    'MAGICLINK_LOGIN_FAILED_TEMPLATE_NAME',
    'tahoe_idp/magiclink_login_failed.html'
)
# If LOGIN_FAILED_REDIRECT has a value the user will be redirected to this
# URL instead of being shown the LOGIN_FAILED_TEMPLATE
LOGIN_FAILED_REDIRECT = getattr(settings, 'MAGICLINK_LOGIN_FAILED_REDIRECT', '')

try:
    TOKEN_LENGTH = int(getattr(settings, 'MAGICLINK_TOKEN_LENGTH', 50))
except ValueError:
    raise ImproperlyConfigured('"MAGICLINK_TOKEN_LENGTH" must be an integer')
else:
    if TOKEN_LENGTH < 20:
        warning = ('Shorter MAGICLINK_TOKEN_LENGTH values make your login more'
                   'sussptable to brute force attacks')
        warnings.warn(warning, RuntimeWarning)

try:
    # In seconds
    AUTH_TIMEOUT = int(getattr(settings, 'MAGICLINK_AUTH_TIMEOUT', 300))
except ValueError:
    raise ImproperlyConfigured('"MAGICLINK_AUTH_TIMEOUT" must be an integer')

try:
    TOKEN_USES = int(getattr(settings, 'MAGICLINK_TOKEN_USES', 1))
except ValueError:
    raise ImproperlyConfigured('"MAGICLINK_TOKEN_USES" must be an integer')

EMAIL_IGNORE_CASE = getattr(settings, 'MAGICLINK_EMAIL_IGNORE_CASE', True)
if not isinstance(EMAIL_IGNORE_CASE, bool):
    raise ImproperlyConfigured('"MAGICLINK_EMAIL_IGNORE_CASE" must be a boolean')

EMAIL_AS_USERNAME = getattr(settings, 'MAGICLINK_EMAIL_AS_USERNAME', True)
if not isinstance(EMAIL_AS_USERNAME, bool):
    raise ImproperlyConfigured('"MAGICLINK_EMAIL_AS_USERNAME" must be a boolean')

ALLOW_SUPERUSER_LOGIN = getattr(settings, 'MAGICLINK_ALLOW_SUPERUSER_LOGIN', True)
if not isinstance(ALLOW_SUPERUSER_LOGIN, bool):
    raise ImproperlyConfigured('"MAGICLINK_ALLOW_SUPERUSER_LOGIN" must be a boolean')

ALLOW_STAFF_LOGIN = getattr(settings, 'MAGICLINK_ALLOW_STAFF_LOGIN', True)
if not isinstance(ALLOW_STAFF_LOGIN, bool):
    raise ImproperlyConfigured('"MAGICLINK_ALLOW_STAFF_LOGIN" must be a boolean')

VERIFY_INCLUDE_EMAIL = getattr(settings, 'MAGICLINK_VERIFY_INCLUDE_EMAIL', True)
if not isinstance(VERIFY_INCLUDE_EMAIL, bool):
    raise ImproperlyConfigured('"MAGICLINK_VERIFY_INCLUDE_EMAIL" must be a boolean')

REQUIRE_SAME_BROWSER = getattr(settings, 'MAGICLINK_REQUIRE_SAME_BROWSER', True)
if not isinstance(REQUIRE_SAME_BROWSER, bool):
    raise ImproperlyConfigured('"MAGICLINK_REQUIRE_SAME_BROWSER" must be a boolean')

REQUIRE_SAME_IP = getattr(settings, 'MAGICLINK_REQUIRE_SAME_IP', True)
if not isinstance(REQUIRE_SAME_IP, bool):
    raise ImproperlyConfigured('"MAGICLINK_REQUIRE_SAME_IP" must be a boolean')

ANONYMIZE_IP = getattr(settings, 'MAGICLINK_ANONYMIZE_IP', True)
if not isinstance(ANONYMIZE_IP, bool):
    raise ImproperlyConfigured('"MAGICLINK_ANONYMIZE_IP" must be a boolean')

ONE_TOKEN_PER_USER = getattr(settings, 'MAGICLINK_ONE_TOKEN_PER_USER', True)
if not isinstance(ONE_TOKEN_PER_USER, bool):
    raise ImproperlyConfigured('"MAGICLINK_ONE_TOKEN_PER_USER" must be a boolean')

try:
    LOGIN_REQUEST_TIME_LIMIT = int(getattr(settings, 'MAGICLINK_LOGIN_REQUEST_TIME_LIMIT', 30))  # In seconds
except ValueError:
    raise ImproperlyConfigured('"MAGICLINK_LOGIN_REQUEST_TIME_LIMIT" must be an integer')

LOGIN_VERIFY_URL = getattr(settings, 'MAGICLINK_LOGIN_VERIFY_URL', 'tahoe_idp:login_verify')

STUDIO_DOMAIN = getattr(settings, 'MAGICLINK_STUDIO_DOMAIN', 'studio.example.com')
