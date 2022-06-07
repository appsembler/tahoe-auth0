"""
Most of the tests here are unique to us. However, the work is Inspired by:
https://github.com/python-social-auth/social-core/blob/master/social_core/backends/
"""
import json
import pytest
from unittest.mock import patch

from httpretty import HTTPretty

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

BASE_URL = "https://domain"

IDP_USER_BODY = {
    "active": True,
    "data": {
        "platform_role": "staff",
    },
    "email": "omar+fusion.auth.trial@appsembler.com",
    "encryptionScheme": "salted-pbkdf2-hmac-sha256",
    "firstName": "Ahmed",
    "id": "2a106a94-c8b0-4f0b-bb69-fea0022c18d8",
    "lastName": "Jazzar",
    "lastUpdateInstant": 1652594234294,
    "tenantId": "aa4a50e3-0d57-d047-6618-0aea1efadf74",
    "username": "ahmedjazzar",
}

ACCESS_TOKEN_BODY = json.dumps(
    {
        "access_token": "foobar",
        "token_type": "bearer",
        "expires_in": 86400,
        "userId": "2a106a94-c8b0-4f0b-bb69-fea0022c18d8",
    }
)


@pytest.mark.usefixtures('mock_tahoe_idp_settings')
class TahoeIdPBackendTest(OAuth2Test):
    backend_path = "tahoe_idp.backend.TahoeIdpOAuth2"
    access_token_body = ACCESS_TOKEN_BODY
    tenant_id = MOCK_TENANT_ID
    expected_username = IDP_USER_BODY['username']
    jwks_url = "{}/.well-known/jwks.json".format(BASE_URL)

    def extra_settings(self):
        settings = super().extra_settings()
        settings["SOCIAL_AUTH_" + self.name + "_BASE_URL"] = BASE_URL
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
    @patch('tahoe_idp.helpers.fusionauth_retrieve_user')
    def test_login(self, mock_fa_retrieve_user):
        mock_fa_retrieve_user.return_value = IDP_USER_BODY
        self.do_login()

    @mock_tahoe_idp_api_settings
    @patch('tahoe_idp.helpers.fusionauth_retrieve_user')
    def test_partial_pipeline(self, mock_fa_retrieve_user):
        mock_fa_retrieve_user.return_value = IDP_USER_BODY
        self.do_partial_pipeline()

    @mock_tahoe_idp_api_settings
    def test_auth_params(self, *args):
        auth_params = self.backend.auth_params()
        assert "tenantId" in auth_params
        assert auth_params["tenantId"] == MOCK_TENANT_ID

    @mock_tahoe_idp_api_settings
    def test_authorization_url(self, *args):
        backend = self.backend
        assert backend.authorization_url() == "{}/oauth2/authorize".format(BASE_URL), 'by default use login url'

        backend.strategy.session_set("auth_entry", "login")
        assert backend.authorization_url() == "{}/oauth2/authorize".format(BASE_URL), "use login url when specified"

        backend.strategy.session_set("auth_entry", "register")
        assert backend.authorization_url() == "{}/oauth2/register".format(BASE_URL), "use register url when specified"

    @mock_tahoe_idp_api_settings
    def test_access_token_url(self, *args):
        self.assertEqual(
            self.backend.access_token_url(),
            "{}/oauth2/token".format(BASE_URL),
        )

    @mock_tahoe_idp_api_settings
    def test_fields_stored_in_session_setting(self, *args):
        backend = self.backend

        assert backend.setting("OTHER_SETTING") is None, "Sanity check: other variables should not be affected"
        assert backend.setting("FIELDS_STORED_IN_SESSION") == ["auth_entry"], "Store auth_entry in session by default"
        assert backend.setting("FIELDS_STORED_IN_SESSION", ["other"]) == ["other"], "Explicit default is respected"

    @mock_tahoe_idp_api_settings
    def test_revoke_token_url(self, *args):
        self.assertEqual(
            self.backend.revoke_token_url("token", "uid"),
            "{}/oauth2/logout".format(BASE_URL),
        )

    def test_get_user_id(self):
        user_id = self.backend.get_user_id({'tahoe_idp_uuid': '2a106a94-c8b0-4f0b-bb69-fea0022c18d8'}, {})
        assert user_id == '2a106a94-c8b0-4f0b-bb69-fea0022c18d8'

    @patch('tahoe_idp.helpers.fusionauth_retrieve_user')
    def test_get_user_details(self, mock_get_idp_user):
        mock_get_idp_user.return_value = {
            "email": "ahmed@appsembler.com",
            "fullName": "Ahmed Jazzar",
            "id": "2a106a94-c8b0-4f0b-bb69-fea0022c18d8",
            "tenantId": "aa4a50e3-0d57-d047-6618-0aea1efadf74",
            "data": {
                "platform_role": "staff",
            },
        }

        user_details = self.backend.get_user_details({
            "userId": "2a106a94-c8b0-4f0b-bb69-fea0022c18d8",
        })

        assert user_details == {
            "username": "2a106a94-c8b0-4f0b-bb69-fea0022c18d8",  # Username not provided, using UUID as username
            "email": "ahmed@appsembler.com",
            "fullname": "Ahmed Jazzar",
            "tahoe_idp_uuid": "2a106a94-c8b0-4f0b-bb69-fea0022c18d8",
            "tahoe_idp_metadata": {
                "platform_role": "staff",
            },
            "tahoe_idp_is_organization_admin": False,
            "tahoe_idp_is_organization_staff": True,
        }

    @patch('tahoe_idp.helpers.fusionauth_retrieve_user')
    def test_build_user_details_with_no_role_or_app_metadata(self, mock_get_idp_user):
        """
        Ensure the backend don't fail on missing `app_metadata`.

        It should assume a safe default role (Learner).
        """
        mock_get_idp_user.return_value = {
          "email": "ahmed@appsembler.com",
          "id": "2a106a94-c8b0-4f0b-bb69-fea0022c18d8",
          "tenantId": "aa4a50e3-0d57-d047-6618-0aea1efadf74",
          "username": "ahmedjazzar",
        }

        user_details = self.backend.get_user_details({
            "userId": "2a106a94-c8b0-4f0b-bb69-fea0022c18d8",
        })

        assert user_details == {
            "username": "ahmedjazzar",
            "email": "ahmed@appsembler.com",
            "fullname": "ahmedjazzar",  # fullNAme not provided, using `username` as full name
            "tahoe_idp_uuid": "2a106a94-c8b0-4f0b-bb69-fea0022c18d8",
            "tahoe_idp_metadata": {},
            "tahoe_idp_is_organization_admin": False,
            "tahoe_idp_is_organization_staff": False,
        }
