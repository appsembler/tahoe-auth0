"""
Tahoe Identity Provider backend.
"""

from social_core.backends.oauth import BaseOAuth2

from .constants import BACKEND_NAME
from . import helpers

from .permissions import (
    get_role_with_default,
    is_course_author,
    is_organization_admin,
    is_organization_staff,
)


class TahoeIdpOAuth2(BaseOAuth2):
    name = BACKEND_NAME

    ACCESS_TOKEN_METHOD = "POST"  # nosec
    REDIRECT_STATE = False
    REVOKE_TOKEN_METHOD = "GET"  # nosec

    def setting(self, name, default=None):
        """
        Override setting to ensure `auth_entry` is stored in session.
        """
        if name == "FIELDS_STORED_IN_SESSION" and not default:
            default = ["auth_entry"]
        return super().setting(name, default)

    def auth_params(self, state=None):
        """
        Overrides the parent's class `auth_params` to add the organization parameter
        to the auth request.
        The API requires us to pass the tenant ID since we are not going
        to ask the user to manually enter their organization name in the login form.
        If we decide against this, we need to enable `Display Organization Prompt` in
        FusionAuth Management Console.
        """
        params = super().auth_params(state=state)
        params["tenantId"] = helpers.get_tenant_id()
        return params

    def get_key_and_secret(self):
        """Return tuple with Consumer Key and Consumer Secret for current
        service provider. Must return (key, secret), order *must* be respected.
        """
        oauth_configs = helpers.get_key_and_secret()
        return oauth_configs['key'], oauth_configs['secret']

    def authorization_url(self):
        auth_entry = self.strategy.session_get('auth_entry')

        endpoint = 'authorize'
        if auth_entry == 'register':
            endpoint = 'register'

        return "{base}/oauth2/{endpoint}".format(
            endpoint=endpoint,
            base=helpers.get_idp_base_url(),
        )

    def access_token_url(self):
        return "{}/oauth2/token".format(helpers.get_idp_base_url())

    def revoke_token_url(self, token, uid):
        return "{}/oauth2/logout".format(helpers.get_idp_base_url())

    def get_user_id(self, details, response):
        """
        Return current permanent user id.
        A payload's userId value contains FusionAuth's unique user uuid;
        similar to this: 2a106a94-c8b0-4f0b-bb69-fea0022c18d8
        """
        return details["tahoe_idp_uuid"]

    def get_user_details(self, response):
        """
        Fetches the user details from response's JWT and build the social_core JSON object.
        """
        tahoe_idp_uuid = response["userId"]
        idp_user = helpers.fusionauth_retrieve_user(tahoe_idp_uuid)

        user_data = idp_user.get("data", {})
        user_data_role = get_role_with_default(user_data)
        username = idp_user.get("username", idp_user["id"])

        return {
            "username": username,
            "email": idp_user["email"],
            "fullname": idp_user.get("fullName", username),
            "tahoe_idp_uuid": idp_user["id"],
            "tahoe_idp_metadata": idp_user.get("data", {}),
            "tahoe_idp_is_course_author": is_course_author(user_data_role),
            "tahoe_idp_is_organization_admin": is_organization_admin(user_data_role),
            "tahoe_idp_is_organization_staff": is_organization_staff(user_data_role),
        }
