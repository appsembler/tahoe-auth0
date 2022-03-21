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

from social_django.models import UserSocialAuth

from .api_client import Auth0ApiClient
from .constants import BACKEND_NAME


def request_password_reset(email):
    """
    Start password reset email for Username|Password Database Connection users.
    """
    auth0_api_client = Auth0ApiClient()
    return auth0_api_client.change_password_via_reset_for_db_connection(email)


def get_auth0_id_by_user(user):
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
    auth0_user_id = get_auth0_id_by_user(user)
    return auth0_api_client.update_user(auth0_user_id, properties)


def update_user_email(user, email, set_email_as_verified=False):
    """
    Update user email via PATCH /api/v2/users/.
    """
    properties = {'email': email}

    if set_email_as_verified:
        properties['email_verified'] = True

    update_user(user, properties=properties)
