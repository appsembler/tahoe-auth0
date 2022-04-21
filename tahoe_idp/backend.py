"""
Auth0 backend.
"""
from urllib import request

from jose import jwt
from social_core.backends.oauth import BaseOAuth2

from .api_client import Auth0ApiClient
from .constants import BACKEND_NAME
from .helpers import get_idp_domain

from .permissions import (
    get_role_with_default,
    is_organization_admin,
    is_organization_staff,
)


def get_api_client():
    return Auth0ApiClient()


def get_jwt_payload(client_id, response):
    """
    Verifies and returns a JWT token payload from the response. A normal returned
    payload looks like the following:
        {
            'iss': 'https://<tenant>.us.auth0.com/',
            'name': 'Ahmed Jazzar',
            'email_verified': False,
            'picture': 'https://s.gravatar.com/avatar/abcd.png',
            'exp': 1633164125,
            'sub': 'auth0|61578ee61e38d9006859b612',
            'email': 'ahmed@appsembler.com',
            'updated_at': '2021-10-01T22:42:54.841Z',
            'iat': 1633128125,
            'nickname': 'ahmed+w0crpcxx7rirspdang',
            'org_id': 'org_2ud2MmLH8vB35m01',
            'aud': '9TbUCXJ9F3u3Q5jyRpOWuKaybiCk3rEa'
        }
    """
    id_token = response.get("id_token")

    issuer = "https://{}/".format(get_idp_domain())
    audience = client_id
    jwks = request.urlopen(  # nosec
        "https://{}/.well-known/jwks.json".format(get_idp_domain())
    )

    return jwt.decode(
        id_token,
        bytearray(jwks.read()).decode("ascii"),
        algorithms=["RS256"],
        audience=audience,
        issuer=issuer,
    )


class TahoeFusionAuthOAuth2(BaseOAuth2):
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
        params["organization"] = get_api_client().organization_id
        return params

    def authorization_url(self):
        return "https://{}/authorize".format(get_idp_domain())

    def access_token_url(self):
        return "https://{}/oauth/token".format(get_idp_domain())

    def revoke_token_url(self, token, uid):
        return "https://{}/logout".format(get_idp_domain())

    def get_user_id(self, details, response):
        """
        Return current permanent user id.

        A payload's sub value contains Auth0's unique user ID; similar
        to this: auth0|61578ee61e38d9006859b612
        """
        client_id = self.setting("KEY")  # CLIENT_ID
        payload = get_jwt_payload(client_id, response)
        return payload["sub"]

    def get_user_details(self, response):
        """
        Fetches the user details from response's JWT and build the social_core JSON object.
        """
        client_id = self.setting("KEY")  # CLIENT_ID
        jwt_payload = get_jwt_payload(client_id, response)
        auth0_user = get_api_client().get_user(jwt_payload["email"])
        fullname, first_name, last_name = self.get_user_names(
            fullname=auth0_user.get("name")
        )
        app_metadata = auth0_user.get('app_metadata', {})
        metadata_role = get_role_with_default(app_metadata)

        nickname = auth0_user.get("nickname", jwt_payload.get("sub"))

        return {
            "username": auth0_user.get("username", nickname),
            "email": auth0_user.get("email"),
            "fullname": fullname,
            "first_name": first_name,
            "last_name": last_name,
            "auth0_is_organization_admin": is_organization_admin(metadata_role),
            "auth0_is_organization_staff": is_organization_staff(metadata_role),
        }
