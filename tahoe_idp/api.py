"""
External Python API helpers goes here.

### API Contract:
 * Those APIs should be stable and abstract internal model changes.

 * Non-stable and internal APIs they should be placed in the `helpers.py` module instead.

 * The parameters of existing functions should change in a backward compatible way:
   - No parameters should be removed from the function
   - New parameters should have safe defaults
 * For breaking changes, new functions should be created
"""

import crum
from social_django.models import UserSocialAuth
from tahoe_sites.api import get_site_by_uuid

from .api_client import Auth0ApiClient
from .constants import BACKEND_NAME


class TahoeIdpStudioException(AttributeError):
    pass


def request_password_reset(email):
    """
    Start password reset email for Username|Password Database Connection users.
    """
    auth0_api_client = Auth0ApiClient()
    return auth0_api_client.change_password_via_reset_for_db_connection(email)


def get_tahoe_idp_id_by_user(user):
    """
    Get auth0 unique ID for a Django user.

    This helper uses the `social_django` app.
    """
    if not user:
        raise ValueError('User should be provided')

    if user.is_anonymous:
        raise ValueError('Non-anonymous User should be provided')

    social_auth_entry = UserSocialAuth.objects.get(
        user=user, provider=BACKEND_NAME,
    )
    return social_auth_entry.uid


def update_user(user, properties):
    """
    Update Auth0 user properties via PATCH /api/v2/users/.

    See: https://auth0.com/docs/api/management/v2#!/Users/patch_users_by_id
    """
    auth0_api_client = Auth0ApiClient()
    auth0_user_id = get_tahoe_idp_id_by_user(user)
    return auth0_api_client.update_user(auth0_user_id, properties)


def update_user_email(user, email, set_email_as_verified=False):
    """
    Update user email via PATCH /api/v2/users/.
    """
    properties = {'email': email}

    if set_email_as_verified:
        properties['email_verified'] = True

    update_user(user, properties=properties)


def save_studio_site_uuid_in_session(studio_site_uuid):
    """
    Saves the value of studio_site_uuid in the session after verifying that:
    - Session exist
    - studio_site_uuid is a valid uuid

    :return: saved studio_site_uuid, or None if session or method verification failed
    :raises: ValueError if studio_site_uuid is invalid
    """
    current_request = crum.get_current_request()

    if getattr(current_request, 'session', None) is None:
        return None

    try:
        get_site_by_uuid(studio_site_uuid)
    except Exception:
        raise ValueError('Invalid site uuid cannot be saved in session! ({invalid_uuid})'.format(
            invalid_uuid=studio_site_uuid or 'None'
        ))

    current_request.session['studio_site_uuid'] = studio_site_uuid

    return studio_site_uuid


def get_studio_site():
    """
    Using studio_site_uuid value stored in the session; return the related Site
    """
    current_request = crum.get_current_request()
    print(getattr(current_request, 'session', None))
    print(getattr(current_request, 'session', None) or 'None attr')
    if not hasattr(current_request, 'session') or current_request.session is None:
        raise TahoeIdpStudioException('get_studio_site did not find a session in the request!')

    studio_site_uuid = current_request.session.get('studio_site_uuid')
    print(studio_site_uuid or 'None2')
    if not studio_site_uuid:
        raise TahoeIdpStudioException('get_studio_site did not find studio_site_uuid in the session!')

    return get_site_by_uuid(site_uuid=studio_site_uuid)


def get_studio_site_configuration():
    """
    Using studio_site_uuid value stored in the session; return the related SiteConfiguration
    """
    site = get_studio_site()

    if not getattr(site, 'configuration', None):
        raise TahoeIdpStudioException('get_studio_site_configuration did not a valid site configuration!')

    return site.configuration
