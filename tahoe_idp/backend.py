"""
Auth0 backend.
"""
from urllib import request

import requests
from jose import jwt
from social_core.backends.oauth import BaseOAuth2

from .api_client import FusionAuthApiClient
from .constants import BACKEND_NAME
from .helpers import get_idp_base_url

from .permissions import (
    get_role_with_default,
    is_organization_admin,
    is_organization_staff,
)


def get_api_client():
    return FusionAuthApiClient()


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

    issuer = "{}/".format(get_idp_base_url())
    audience = client_id
    jwks_response = requests.get("{}/.well-known/openid-configuration".format(get_idp_base_url()))
    jwks = jwks_response.content

    return jwt.decode(
        token=id_token,
        key=jwks,
        algorithms=[
            "ES256",
            "ES384",
            "ES512",
            "HS256",
            "HS384",
            "HS512",
            "RS256",
            "RS384",
            "RS512",
        ],
        audience=audience,
        issuer=issuer,
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
        params["organization"] = get_api_client().organization_id
        return params

    def authorization_url(self):
        return "{}/oauth2/authorize".format(get_idp_base_url())

    def access_token_url(self):
        return "{}/oauth2/token".format(get_idp_base_url())

    def revoke_token_url(self, token, uid):
        return "{}/oauth2/logout".format(get_idp_base_url())

    # def get_user_id(self, details, response):
    #     """
    #     Return current permanent user id.
    #
    #     A payload's sub value contains Auth0's unique user ID; similar
    #     to this: auth0|61578ee61e38d9006859b612
    #     """
    #     client_id = self.setting("KEY")  # CLIENT_ID
    #     payload = get_jwt_payload(client_id, response)
    #     return payload["sub"]

    def get_user_details(self, response):
        """
        Fetches the user details from response's JWT and build the social_core JSON object.
        """
        import random

        id_token = response.get("id_token")
        raise Exception(id_token)

        # client_id = self.setting("KEY")  # CLIENT_ID
        # jwt_payload = get_jwt_payload(client_id, response)

        email = 'test+{}@example.com'.format(random.randrange(1, 999999))
        return {
            'fullname': 'test',
            'email': email,
            'tahoe_idp_is_organization_admin': False,
            'tahoe_idp_is_organization_staff': True,
        }
        # client_id = self.setting("KEY")  # CLIENT_ID
        # jwt_payload = get_jwt_payload(client_id, response)
        # auth0_user = get_api_client().get_user(jwt_payload["email"])
        # fullname, first_name, last_name = self.get_user_names(
        #     fullname=auth0_user.get("name")
        # )
        # app_metadata = auth0_user.get('app_metadata', {})
        # metadata_role = get_role_with_default(app_metadata)
        #
        # nickname = auth0_user.get("nickname", jwt_payload.get("sub"))
        #
        # return {
        #     "username": auth0_user.get("username", nickname),
        #     "email": auth0_user.get("email"),
        #     "fullname": fullname,
        #     "first_name": first_name,
        #     "last_name": last_name,
        #     "tahoe_idp_is_organization_admin": is_organization_admin(metadata_role),
        #     "tahoe_idp_is_organization_staff": is_organization_staff(metadata_role),
        # }
