"""
Auth0 backend.
"""
from urllib import request

from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from jose import jwt
from social_core.backends.oauth import BaseOAuth2
from social_core.utils import handle_http_errors
from tahoe_idp.api import get_studio_site, get_studio_site_configuration

from tahoe_sites.api import get_organization_by_site, is_active_admin_on_organization
from .api_client import Auth0ApiClient
from .constants import BACKEND_NAME
from .helpers import get_idp_domain
from .permissions import (
    get_role_with_default,
    is_organization_admin,
    is_organization_staff,
)


class TahoeIdpOAuth2(BaseOAuth2):
    """A python Social Auth OAuth authentication Backend hooked with Auth0"""

    name = BACKEND_NAME

    ACCESS_TOKEN_METHOD = "POST"  # nosec
    REDIRECT_STATE = False
    REVOKE_TOKEN_METHOD = "GET"  # nosec

    @property
    def client(self):
        return Auth0ApiClient()

    @property
    def idp_domain(self):
        return get_idp_domain()

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

        issuer = "https://{}/".format(self.idp_domain)
        audience = self.setting("KEY")  # CLIENT_ID
        jwks = request.urlopen(  # nosec
            "https://{}/.well-known/jwks.json".format(self.idp_domain)
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
        params = super().auth_params(state=state)
        params["organization"] = self.client.organization_id
        return params

    def authorization_url(self):
        return "https://{}/authorize".format(self.idp_domain)

    def access_token_url(self):
        return "https://{}/oauth/token".format(self.idp_domain)

    def revoke_token_url(self, token, uid):
        return "https://{}/logout".format(self.idp_domain)

    def get_user_id(self, details, response):
        """
        Return current permanent user id.

        A payload's sub value contains Auth0's unique user ID; similar
        to this: auth0|61578ee61e38d9006859b612
        """
        payload = self._get_payload(response)
        return payload["sub"]

    def _build_user_details(self, jwt_payload, auth0_user):
        """
        Build user details from jwt_payload and auth0 user info from the API.
        """
        app_metadata = auth0_user.get('app_metadata', {})
        metadata_role = get_role_with_default(app_metadata)

        nickname = auth0_user.get("nickname", jwt_payload.get("sub"))
        fullname, first_name, last_name = self.get_user_names(
            fullname=auth0_user.get("name")
        )

        return {
            "username": auth0_user.get("username", nickname),
            "email": auth0_user.get("email"),
            "fullname": fullname,
            "first_name": first_name,
            "last_name": last_name,
            "tahoe_idp_is_organization_admin": is_organization_admin(metadata_role),
            "tahoe_idp_is_organization_staff": is_organization_staff(metadata_role),
        }

    def get_user_details(self, response):
        """
        Fetches the user details from response's JWT and build the social_core JSON object.
        """
        jwt_payload = self._get_payload(response)
        auth0_user = self.client.get_user(jwt_payload["email"])
        return self._build_user_details(jwt_payload=jwt_payload, auth0_user=auth0_user)


class StudioTahoeIdpOAuth2(TahoeIdpOAuth2):
    """
    Backend for studio
    """
    @property
    def client(self):
        return Auth0ApiClient(site_configuration=get_studio_site_configuration())

    @property
    def idp_domain(self):
        return get_idp_domain(site_configuration=get_studio_site_configuration())

    @handle_http_errors
    def do_auth(self, access_token, *args, **kwargs):
        """
        Override to allow only staff and admin users
        """
        result = super(StudioTahoeIdpOAuth2, self).do_auth(access_token=access_token, *args, **kwargs)

        if isinstance(result, HttpResponseRedirect):
            if result.url == '/register':
                return self.redirect_to_lms_login(next_url='/studio')
            return result

        if result.is_active and (result.is_superuser or result.is_staff):
            return result

        organization = get_organization_by_site(get_studio_site())
        if not is_active_admin_on_organization(user=result, organization=organization):
            return redirect(reverse('tahoe_idp:no_studio_access'), perminant=False)

        return result
