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

from .constants import BACKEND_NAME
from . import helpers


def request_password_reset(email):
    """
    Start password reset email for Username|Password Database Connection users.
    """
    api_client = helpers.get_api_client()
    client_response = api_client.forgot_password({'loginId': email})
    http_response = client_response.response
    http_response.raise_for_status()
    return http_response


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
    Update Auth0 user properties via PATCH /api/user/{userId}.

    See: https://fusionauth.io/docs/v1/tech/apis/users#update-a-user
    """
    api_client = helpers.get_api_client()
    idp_user_id = get_tahoe_idp_id_by_user(user)
    client_response = api_client.patch_user(
        user_id=idp_user_id,
        request=properties,
    )
    http_response = client_response.response
    http_response.raise_for_status()
    return http_response


def update_user_email(user, email, set_email_as_verified=False):
    """
    Update user email via PATCH /api/user/{userId}.
    """
    properties = {
        'user': {
            'email': email,
        },
    }

    if set_email_as_verified:
        properties['skipVerification'] = True

    return update_user(user, properties=properties)
