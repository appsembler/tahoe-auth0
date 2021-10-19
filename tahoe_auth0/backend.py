"""
Auth0 backend.
"""
from urllib import request

from jose import jwt
from social_core.backends.oauth import BaseOAuth2

from tahoe_auth0.api_client import Auth0ApiClient


class TahoeAuth0OAuth2(BaseOAuth2):
    """A python Social Auth OAuth authentication Backend hooked with Auth0"""

    name = "tahoe-auth0"

    ACCESS_TOKEN_METHOD = "POST"
    REDIRECT_STATE = False
    REVOKE_TOKEN_METHOD = "GET"

    @property
    def client(self):
        return Auth0ApiClient()

    def _get_payload(self, response):
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

        issuer = "https://{}/".format(self.client.domain)
        audience = self.setting("KEY")  # CLIENT_ID
        jwks = request.urlopen(
            "https://{}/.well-known/jwks.json".format(self.client.domain)
        )

        return jwt.decode(
            id_token,
            bytearray(jwks.read()).decode("ascii"),
            algorithms=["RS256"],
            audience=audience,
            issuer=issuer,
        )

    def auth_params(self, state=None):
        """
        Overrides the parent's class `auth_params` to add the organization parameter
        to the auth request.
        The Auth0 API requires us to pass the organization ID since we are not going
        to ask the user to manually enter their organization name in the login form.
        If we decide against this, we need to enable `Display Organization Prompt` in
        Auth0 Management Console.
        """
        params = super(TahoeAuth0OAuth2, self).auth_params(state=state)
        params["organization"] = self.client.organization_id

        return params

    def authorization_url(self):
        return "https://{}/authorize".format(self.client.domain)

    def access_token_url(self):
        return "https://{}/oauth/token".format(self.client.domain)

    def revoke_token_url(self, token, uid):
        return "https://{}/logout".format(self.client.domain)

    def get_user_id(self, details, response):
        """
        Return current permanent user id.

        A payload's sub value contains Auth0's unique user ID; similar
        to this: auth0|61578ee61e38d9006859b612
        """
        payload = self._get_payload(response)
        return payload["sub"]

    def get_user_details(self, response):
        """
        Fetches the user details from response's JWT.
        """
        payload = self._get_payload(response)
        user_details = self.client.get_user(payload["email"])

        nickname = user_details.get("nickname", payload.get("sub"))
        fullname, first_name, last_name = self.get_user_names(
            fullname=user_details.get("name")
        )

        return {
            "username": user_details.get("username", nickname),
            "email": user_details.get("email"),
            "fullname": fullname,
            "first_name": first_name,
            "last_name": last_name,
        }
