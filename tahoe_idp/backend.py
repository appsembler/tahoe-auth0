"""
Tahoe Identity Provider backend.
"""

from social_core.backends.oauth import BaseOAuth2


from .constants import BACKEND_NAME
from . import helpers

from .permissions import (
    get_role_with_default,
    is_organization_admin,
    is_organization_staff,
)


class TahoeIdpOAuth2(BaseOAuth2):
    name = BACKEND_NAME

    ACCESS_TOKEN_METHOD = "POST"  # nosec
    REDIRECT_STATE = False
    REVOKE_TOKEN_METHOD = "GET"  # nosec

    def auth_params(self, state=None):
        """
        Overrides the parent's class `auth_params` to add the organization parameter
        to the auth request.
        The Auth0 API requires us to pass the organization ID since we are not going
        to ask the user to manually enter their organization name in the login form.
        If we decide against this, we need to enable `Display Organization Prompt` in
        Auth0 Management Console.
        """
        params = super().auth_params(state=state)
        params["tenantId"] = helpers.get_tenant_id()
        return params

    def authorization_url(self):
        return "{}/oauth2/authorize".format(helpers.get_idp_base_url())

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
        id_token = response["id_token"]
        client_id = self.setting("KEY")  # CLIENT_ID

        idp_user = helpers.get_idp_user_from_id_token(client_id, id_token)

        first_name = idp_user["firstName"]
        last_name = idp_user["lastName"]
        fullname = "{first_name} {last_name}".format(first_name=first_name, last_name=last_name)

        user_data = idp_user.get("data", {})
        user_data_role = get_role_with_default(user_data)

        return {
            "username": idp_user.get("username", idp_user["id"]),
            "email": idp_user["email"],
            "fullname": fullname,
            "first_name": first_name,
            "last_name": last_name,
            "tahoe_idp_uuid": idp_user["id"],
            "tahoe_idp_is_organization_admin": is_organization_admin(user_data_role),
            "tahoe_idp_is_organization_staff": is_organization_staff(user_data_role),
        }
