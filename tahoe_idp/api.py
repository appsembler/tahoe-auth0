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

from datetime import datetime
import pytz
from social_django.models import UserSocialAuth

from urllib.parse import urlencode

from .constants import BACKEND_NAME
from . import helpers


def request_password_reset(email):
    """
    Start password reset email for Username|Password Database Connection users.
    """
    api_client = helpers.get_api_client()
    client_response = api_client.forgot_password({'loginId': email})
    http_response = helpers.get_successful_fusion_auth_http_response(client_response)
    return http_response


def get_logout_url(post_logout_redirect_uri):
    """
    Get Tahoe IdP URL.
    """
    tenant_id = helpers.get_tenant_id()
    client_configs = helpers.get_key_and_secret()
    base_url = helpers.get_idp_base_url()

    query_params = (
        ('tenantId', tenant_id),
        ('client_id', client_configs['key']),
        ('post_logout_redirect_uri', post_logout_redirect_uri),
    )

    return '{base}/oauth2/logout?{query}'.format(
        base=base_url,
        query=urlencode(query_params),
    )


def get_tahoe_idp_id_by_user(user):
    """
    Get Tahoe IdP unique ID for a Django user.

    This helper uses the `social_django` app.
    """
    if not user:
        raise ValueError('User should be provided')

    if user.is_anonymous:
        raise ValueError('Non-anonymous User should be provided')

    social_auth_entry = UserSocialAuth.objects.get(
        user_id=user.id, provider=BACKEND_NAME,
    )
    return social_auth_entry.uid


def update_user(user, properties):
    """
    Update user properties via PATCH /api/user/{userId}.

    See: https://fusionauth.io/docs/v1/tech/apis/users#update-a-user
    """
    api_client = helpers.get_api_client()
    idp_user_id = get_tahoe_idp_id_by_user(user)
    client_response = api_client.patch_user(
        user_id=idp_user_id,
        request=properties,
    )
    http_response = helpers.get_successful_fusion_auth_http_response(client_response)
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


def update_tahoe_user_id(user, now=None):
    """
    Store the Tahoe `User.id` in FusionAuth via PATCH /api/user/.
    """
    if not now:
        now = datetime.now(pytz.utc)

    now_str = str(now.isoformat())

    properties = {
        'user': {
            'data': {
                'tahoe_user_id': user.id,
                'tahoe_user_last_login': now_str,
            },
        },
    }

    return update_user(user, properties=properties)


def deactivate_user(idp_user_id):
    """
    Soft delete the IdP user account.

    This deactivates the user. Permanent deletion is still needed.

    See: https://fusionauth.io/docs/v1/tech/apis/users#delete-a-user
    """
    api_client = helpers.get_api_client()
    client_response = api_client.deactivate_user(
        user_id=idp_user_id,
    )
    http_response = helpers.get_successful_fusion_auth_http_response(client_response)
    return http_response
