"""
Most of the tests here are unique to us. However, the work is Inspired by:
https://github.com/python-social-auth/social-core/blob/master/social_core/backends/auth0.py
"""
import json
import pytest
from unittest.mock import patch

from httpretty import HTTPretty
from jose import jwt

from tahoe_idp.backend import TahoeIdpOAuth2

from .oauth import OAuth2Test
from .conftest import mock_tahoe_idp_api_settings, MOCK_TENANT_ID


JWK_KEY = {
    "kty": "RSA",
    "d": "ZmswNokEvBcxW_Kvcy8mWUQOQCBdGbnM0xR7nhvGHC-Q24z3XAQWlMWbsmGc_R1o"
    "_F3zK7DBlc3BokdRaO1KJirNmnHCw5TlnBlJrXiWpFBtVglUg98-4sRRO0VWnGXK"
    "JPOkBQ6b_DYRO3b0o8CSpWowpiV6HB71cjXTqKPZf-aXU9WjCCAtxVjfIxgQFu5I"
    "-G1Qah8mZeY8HK_y99L4f0siZcbUoaIcfeWBhxi14ODyuSAHt0sNEkhiIVBZE7QZ"
    "m-SEP1ryT9VAaljbwHHPmg7NC26vtLZhvaBGbTTJnEH0ZubbN2PMzsfeNyoCIHy4"
    "4QDSpQDCHfgcGOlHY_t5gQ",
    "e": "AQAB",
    "use": "sig",
    "kid": "foobar",
    "alg": "RS256",
    "n": "pUfcJ8WFrVue98Ygzb6KEQXHBzi8HavCu8VENB2As943--bHPcQ-nScXnrRFAUg8"
    "H5ZltuOcHWvsGw_AQifSLmOCSWJAPkdNb0w0QzY7Re8NrPjCsP58Tytp5LicF0Ao"
    "Ag28UK3JioY9hXHGvdZsWR1Rp3I-Z3nRBP6HyO18pEgcZ91c9aAzsqu80An9X4DA"
    "b1lExtZorvcd5yTBzZgr-MUeytVRni2lDNEpa6OFuopHXmg27Hn3oWAaQlbymd4g"
    "ifc01oahcwl3ze2tMK6gJxa_TdCf1y99Yq6oilmVvZJ8kwWWnbPE-oDmOVPVnEyT"
    "vYVCvN4rBT1DQ-x0F1mo2Q",
}

JWK_PUBLIC_KEY = {key: value for key, value in JWK_KEY.items() if key != "d"}

# patch_get_user = patch.object(
#     FusionAuthApiClient, "get_user", return_value={"username": expected_username}
# )
# patch_get_access_token = patch.object(FusionAuthApiClient, "_get_access_token")
# patch_get_org_id = patch.object(
#     FusionAuthApiClient, "_get_auth0_tenant_id", return_value=tenant_id
# )
# return patch_get_user(patch_get_access_token(patch_get_org_id(test_func)))


@pytest.mark.usefixtures('mock_tahoe_idp_settings')
class Auth0Test(OAuth2Test):
    backend_path = "tahoe_idp.backend.TahoeIdpOAuth2"
    base_url = "https://domain.world"
    access_token_body = json.dumps(
        {
            "access_token": "foobar",
            "token_type": "bearer",
            "expires_in": 86400,
            "id_token": jwt.encode(
                {
                    "nickname": "foobar",
                    "email": "foobar@auth0.com",
                    "name": "John Doe",
                    "picture": "http://example.com/image.png",
                    "sub": "123456",
                    "iss": "{}/".format(base_url),
                },
                JWK_KEY,
                algorithm="RS256",
            ),
        }
    )
    expected_username = "foobar"
    tenant_id = MOCK_TENANT_ID
    jwks_url = "{}/.well-known/jwks.json".format(base_url)

    def extra_settings(self):
        settings = super().extra_settings()
        settings["SOCIAL_AUTH_" + self.name + "_DOMAIN"] = self.base_url
        return settings

    def auth_handlers(self, start_url):
        HTTPretty.register_uri(
            HTTPretty.GET,
            self.jwks_url,
            body=json.dumps({"keys": [JWK_PUBLIC_KEY]}),
            content_type="application/json",
        )
        return super().auth_handlers(start_url)

    @mock_tahoe_idp_api_settings
    def test_login(self, *args):
        self.do_login()

    @mock_tahoe_idp_api_settings
    def test_partial_pipeline(self, *args):
        self.do_partial_pipeline()

    @mock_tahoe_idp_api_settings
    def test_auth_params(self, *args):
        auth_params = self.backend.auth_params()
        assert "tenantId" in auth_params
        assert auth_params["tenantId"] == MOCK_TENANT_ID

    @mock_tahoe_idp_api_settings
    def test_authorization_url(self, *args):
        self.assertEqual(
            self.backend.authorization_url(), "{}/oauth2/authorize".format(self.base_url)
        )

    @mock_tahoe_idp_api_settings
    def test_access_token_url(self, *args):
        self.assertEqual(
            self.backend.access_token_url(),
            "{}/oauth2/token".format(self.base_url),
        )

    @mock_tahoe_idp_api_settings
    def test_revoke_token_url(self, *args):
        self.assertEqual(
            self.backend.revoke_token_url("token", "uid"),
            "{}/oauth2/logout".format(self.base_url),
        )

    @mock_tahoe_idp_api_settings
    @patch('tahoe_idp.helpers.get_jwt_payload')
    def test_get_user_id(self, mock_get_payload, *args):
        id_token = self.get_id_token()
        mock_get_payload.return_value = id_token

        user_id = self.backend.get_user_id("details", "response")

        self.assertEqual(user_id, id_token["sub"])

    @patch.object(TahoeIdpOAuth2, "get_jwt_payload")
    @mock_tahoe_idp_api_settings
    def test_get_user_details(self, mock_get_user, *args):
        mock_get_user.return_value = {
            "username": self.expected_username,
            "email": "ahmed@appsembler.com",
            "name": "Ahmed Jazzar",
            "app_metadata": {
                "role": "Staff",
            }
        }

        user_details = self.backend.get_user_details("response")
        self.assertEqual(
            user_details,
            {
                "username": self.expected_username,
                "email": "ahmed@appsembler.com",
                "fullname": "Ahmed Jazzar",
                "first_name": "Ahmed",
                "last_name": "Jazzar",
                "auth0_is_organization_admin": False,
                "auth0_is_organization_staff": True,
            },
        )

    def test_build_user_details_with_no_role_or_app_metadata(self):
        """
        Ensure the backend don't fail on missing `app_metadata`.

        It should assume a safe default role (Learner).
        """
        auth0_user = {
            "username": self.expected_username,
            "email": "ahmed@appsembler.com",
            "name": "Ahmed Jazzar",
            # Not passing `app_metadata` on purpose.
        }
        jwt_payload = {
            "sub": "auth0|a0d9hszw742wd7hkgwha",
        }

        user_details = self.backend.get_user_details(
            jwt_payload=jwt_payload,
            auth0_user=auth0_user,
        )
        self.assertEqual(
            user_details,
            {
                "username": self.expected_username,
                "email": "ahmed@appsembler.com",
                "fullname": "Ahmed Jazzar",
                "first_name": "Ahmed",
                "last_name": "Jazzar",
                "auth0_is_organization_admin": False,
                "auth0_is_organization_staff": False,
            },
        )

    def get_id_token(self):
        access_token = json.loads(self.access_token_body)
        return jwt.decode(
            access_token["id_token"],
            JWK_KEY,
            algorithms=["RS256"],
            options={"verify_signature": False},
        )
