"""
Auth0 backend.
"""
from urllib import request

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from jose import jwt
from social_core.backends.oauth import BaseOAuth2


class Auth0(BaseOAuth2):
    """Auth0 OAuth authentication backend"""

    name = "tahoe-auth0"

    ACCESS_TOKEN_METHOD = "POST"
    REDIRECT_STATE = False
    REVOKE_TOKEN_METHOD = "GET"

    @property
    def auth0_domain(self):
        """
        A helper method to fetch auth0 domain from the lms FEATURES env settings.
        """
        domain = settings.FEATURES.get("AUTH0_DOMAIN")

        if not domain:
            raise ImproperlyConfigured(
                "We were not able to find AUTH0_DOMAIN in your settings.FEATURES"
            )

        return domain

    def _get_payload(self, response):
        """
        Verifies and returns a JWT token payload from the response
        """
        id_token = response.get("id_token")
        issuer = "https://{}/".format(self.auth0_domain)
        audience = self.setting("KEY")  # CLIENT_ID
        jwks = request.urlopen(
            "https://{}/.well-known/jwks.json".format(self.auth0_domain)
        )

        return jwt.decode(
            id_token,
            jwks.read(),
            algorithms=["RS256"],
            audience=audience,
            issuer=issuer,
        )

    def authorization_url(self):
        return "https://{}/authorize".format(self.auth0_domain)

    def access_token_url(self):
        return "https://{}/oauth/token".format(self.auth0_domain)

    def revoke_token_url(self, token, uid):
        return "https://{}/logout".format(self.auth0_domain)

    def get_user_id(self, details, response):
        """Return current permanent user id."""
        payload = self._get_payload(response)
        return payload["sub"]

    def get_user_details(self, response):
        """
        Obtain JWT and the keys to validate the signature
        """
        payload = self._get_payload(response)
        return {
            "username": payload["nickname"],
            "first_name": payload["name"],
            "user_id": payload["sub"],
            "email": payload["email"],
        }

    def user_data(self, access_token, *args, **kwargs):
        """
        Loads user data from Auth0
        """
        info_uri = "https://{}/userinfo".format(self.auth0_domain)
        return self.get_json(info_uri, params={"access_token": access_token})
