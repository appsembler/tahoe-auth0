import pytest
from django.core.exceptions import ImproperlyConfigured
from unittest.mock import patch, Mock

from django.test import TestCase

from site_config_client.openedx.test_helpers import override_site_config
from tahoe_idp.api_client import Auth0ApiClient
from .conftest import mock_tahoe_idp_api_settings


@patch.object(Auth0ApiClient, "_get_access_token", Mock(return_value='xyz-token'))
@pytest.mark.usefixtures('mock_tahoe_idp_settings')
class TestAuth0ApiClient(TestCase):
    def test_init(self):
        client = Auth0ApiClient()
        self.assertEqual(client.domain, 'domain.world')
        self.assertEqual(client.access_token, 'xyz-token')

    def test_token_url(self):
        client = Auth0ApiClient()
        self.assertEqual(client.token_url, "https://domain.world/oauth/token")

    def test_users_url(self):
        client = Auth0ApiClient()
        self.assertEqual(client.users_url, "https://domain.world/api/v2/users")

    def test_api_headers(self):
        client = Auth0ApiClient()
        self.assertEqual(
            client.api_headers,
            {
                "Content-Type": "application/json",
                "authorization": "Bearer xyz-token",
            },
        )

    def test_api_identifier(self):
        client = Auth0ApiClient()
        self.assertEqual(client.api_identifier, "https://domain.world/api/v2/")

    @patch.object(Auth0ApiClient, "_get_auth0_organization_id")
    def test_organization_id(self, mock_get_auth0_organization_id):
        client = Auth0ApiClient()
        oid = client.organization_id

        mock_get_auth0_organization_id.assert_called_once_with()
        self.assertEqual(oid, mock_get_auth0_organization_id.return_value)

    @override_site_config('admin', IDP_CONNECTION_ID='con-testxyzid')
    def test_get_connection(self):
        client = Auth0ApiClient()
        self.assertEqual(client.get_connection(), 'con-testxyzid')

    @override_site_config('admin', SOME_CONFIG='test')
    def test_get_missing_connection_id(self):
        client = Auth0ApiClient()
        with pytest.raises(ImproperlyConfigured, match='IDP_CONNECTION_ID'):
            client.get_connection()

    @override_site_config('admin', IDP_ORGANIZATION_ID='org_testid')
    def test_get_auth0_organization_id(self):
        client = Auth0ApiClient()
        org_id = client._get_auth0_organization_id()
        self.assertEqual(org_id, 'org_testid')

    @override_site_config('admin', OTHER_CONFIG='some-value')
    def test_get_auth0_organization_id_missing_org_id(self):
        client = Auth0ApiClient()
        with pytest.raises(ImproperlyConfigured, match='IDP_ORGANIZATION_ID'):
            client._get_auth0_organization_id()

    def test_create_user_no_name(self):
        client = Auth0ApiClient()
        with self.assertRaises(KeyError):
            client.create_user({})

    def test_create_user_no_username(self):
        client = Auth0ApiClient()
        with self.assertRaises(KeyError):
            client.create_user({"name": "Ahmed Jazzar"})

    def test_create_user_no_email(self):
        client = Auth0ApiClient()
        with self.assertRaises(KeyError):
            client.create_user(
                {
                    "name": "Ahmed Jazzar",
                    "username": "ahmedjazzar",
                }
            )

    def test_create_user_no_password(self):
        client = Auth0ApiClient()
        with self.assertRaises(KeyError):
            client.create_user(
                {
                    "name": "Ahmed Jazzar",
                    "username": "ahmedjazzar",
                    "email": "ahmed@appsembler.com",
                }
            )

    @patch("tahoe_idp.api_client.requests.post")
    @patch.object(Auth0ApiClient, "get_connection", Mock())
    def test_create_user(self, mock_post):
        client = Auth0ApiClient()
        resp = client.create_user(
            {
                "name": "Ahmed Jazzar",
                "username": "ahmedjazzar",
                "email": "ahmed@appsembler.com",
                "password": "password",
                "some_extra_param": "some_extra_value",
            }
        )

        self.assertEqual(resp, mock_post.return_value)
        mock_post.assert_called_with(
            client.users_url,
            headers=client.api_headers,
            json={
                "name": "Ahmed Jazzar",
                "username": "ahmedjazzar",
                "email": "ahmed@appsembler.com",
                "password": "password",
                "email_verified": False,
                "verify_email": True,
                "connection": client.get_connection(),
                "user_metadata": {
                    "extra_registration_params": {
                        "some_extra_param": "some_extra_value",
                    },
                },
            },
            timeout=10,
        )

    @patch("tahoe_idp.api_client.requests.get")
    @mock_tahoe_idp_api_settings
    @patch("tahoe_idp.api_client.helpers.build_auth0_query")
    def test_get_user(
        self,
        mock_build_auth0_query,
        mock_get,
    ):
        client = Auth0ApiClient()

        query = "test"
        url = client.users_url + "?q={}".format(query)
        mock_build_auth0_query.return_value = query

        user = client.get_user("ahmed@appsembler.com")
        self.assertIsInstance(user, dict)

        mock_get.assert_called_with(url, headers=client.api_headers, timeout=10)


@patch("tahoe_idp.api_client.requests.post")
@patch("tahoe_idp.api_client.helpers.get_idp_base_url")
@patch("tahoe_idp.api_client.helpers.get_client_info")
def test_get_access_token(
    mock_get_client_info, mock_get_idp_base_url, mock_post
):
    client_id = "client"
    client_secret = "secret"
    mock_get_client_info.return_value = (client_id, client_secret)

    client = Auth0ApiClient()
    access_token = client._get_access_token()

    assert access_token == mock_post.return_value.json()["access_token"]

    headers = {"content-type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "audience": client.api_identifier,
    }
    mock_post.assert_called_with(client.token_url, headers=headers, data=data, timeout=10)
