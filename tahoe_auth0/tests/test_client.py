from unittest.mock import PropertyMock, patch

from django.test import TestCase

from tahoe_auth0.api_client import Auth0ApiClient


class TestAuth0ApiClient(TestCase):
    @patch("tahoe_auth0.api_client.helpers.get_auth0_domain")
    @patch.object(Auth0ApiClient, "_get_access_token")
    def test_init(self, mock_get_access_token, mock_get_auth0_domain):
        client = Auth0ApiClient()

        self.assertEqual(client.domain, mock_get_auth0_domain.return_value)
        self.assertEqual(client.access_token, mock_get_access_token.return_value)

    @patch("tahoe_auth0.api_client.helpers.get_auth0_domain")
    @patch.object(Auth0ApiClient, "_get_access_token")
    def test_token_url(self, mock_get_access_token, mock_get_auth0_domain):
        client = Auth0ApiClient()
        self.assertEqual(
            client.token_url,
            "https://{}/oauth/token".format(mock_get_auth0_domain.return_value),
        )

    @patch("tahoe_auth0.api_client.get_current_organization")
    @patch("tahoe_auth0.api_client.helpers.get_auth0_domain")
    @patch.object(Auth0ApiClient, "_get_access_token")
    def test_organization_url(
        self,
        mock_get_access_token,
        mock_get_auth0_domain,
        mock_get_current_organization,
    ):
        client = Auth0ApiClient()
        self.assertEqual(
            client.organization_url,
            "https://{}/api/v2/organizations/name/{}".format(
                mock_get_auth0_domain.return_value,
                mock_get_current_organization.return_value.short_name,
            ),
        )

    @patch("tahoe_auth0.api_client.helpers.get_auth0_domain")
    @patch.object(Auth0ApiClient, "_get_access_token")
    def test_users_url(self, mock_get_access_token, mock_get_auth0_domain):
        client = Auth0ApiClient()
        self.assertEqual(
            client.users_url,
            "https://{}/api/v2/users".format(mock_get_auth0_domain.return_value),
        )

    @patch("tahoe_auth0.api_client.helpers.get_auth0_domain")
    @patch.object(Auth0ApiClient, "_get_access_token")
    def test_api_headers(self, mock_get_access_token, mock_get_auth0_domain):
        client = Auth0ApiClient()
        self.assertEqual(
            client.api_headers,
            {
                "Content-Type": "application/json",
                "authorization": "Bearer {}".format(mock_get_access_token.return_value),
            },
        )

    @patch("tahoe_auth0.api_client.helpers.get_auth0_domain")
    @patch.object(Auth0ApiClient, "_get_access_token")
    def test_api_identifier(self, mock_get_access_token, mock_get_auth0_domain):
        client = Auth0ApiClient()
        self.assertEqual(
            client.api_identifier,
            "https://{}/api/v2/".format(mock_get_auth0_domain.return_value),
        )

    @patch("tahoe_auth0.api_client.helpers.get_auth0_domain")
    @patch.object(Auth0ApiClient, "_get_access_token")
    @patch.object(Auth0ApiClient, "_get_auth0_organization_id")
    def test_organization_id(
        self,
        mock_get_auth0_organization_id,
        mock_get_access_token,
        mock_get_auth0_domain,
    ):
        client = Auth0ApiClient()
        oid = client.organization_id

        mock_get_auth0_organization_id.assert_called_once_with()
        self.assertEqual(oid, mock_get_auth0_organization_id.return_value)

    @patch("tahoe_auth0.api_client.helpers.get_auth0_domain")
    @patch.object(Auth0ApiClient, "_get_access_token")
    @patch.object(Auth0ApiClient, "organization_id")
    def test_get_connection(
        self, mock_organization_id, mock_get_access_token, mock_get_auth0_domain
    ):
        mock_value = "con_someid"
        mock_organization_id.__get__ = PropertyMock(return_value=mock_value)
        client = Auth0ApiClient()

        org_id = mock_value.split("_")[1]
        self.assertEqual("con-{}".format(org_id), client.get_connection())

    @patch("tahoe_auth0.api_client.helpers.get_auth0_domain")
    @patch.object(Auth0ApiClient, "_get_access_token")
    @patch.object(Auth0ApiClient, "organization_id")
    def test_get_connection_unexpected(
        self, mock_organization_id, mock_get_access_token, mock_get_auth0_domain
    ):
        mock_value = "someidnounderscores"
        mock_organization_id.__get__ = PropertyMock(return_value=mock_value)
        client = Auth0ApiClient()

        with self.assertRaises(ValueError):
            client.get_connection()

    @patch("tahoe_auth0.api_client.requests.post")
    @patch("tahoe_auth0.api_client.helpers.get_auth0_domain")
    @patch("tahoe_auth0.api_client.helpers.get_client_info")
    def test_get_access_token(
        self, mock_get_client_info, mock_get_auth0_domain, mock_post
    ):
        client_id = "client"
        client_secret = "secret"
        mock_get_client_info.return_value = (client_id, client_secret)

        client = Auth0ApiClient()
        access_token = client._get_access_token()

        self.assertEqual(access_token, mock_post.return_value.json()["access_token"])

        headers = {"content-type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "audience": client.api_identifier,
        }
        mock_post.assert_called_with(client.token_url, headers=headers, data=data)

    @patch("tahoe_auth0.api_client.requests.get")
    @patch("tahoe_auth0.api_client.helpers.get_auth0_domain")
    @patch.object(Auth0ApiClient, "_get_access_token")
    def test_get_auth0_organization_id(
        self, mock_get_access_token, mock_get_auth0_domain, mock_get
    ):
        client = Auth0ApiClient()
        org_id = client._get_auth0_organization_id()

        self.assertEqual(org_id, mock_get.return_value.json()["id"])
        mock_get.assert_called_with(client.organization_url, headers=client.api_headers)

    @patch("tahoe_auth0.api_client.helpers.get_auth0_domain")
    @patch.object(Auth0ApiClient, "_get_access_token")
    def test_create_user_no_name(self, mock_get_access_token, mock_get_auth0_domain):
        client = Auth0ApiClient()
        with self.assertRaises(KeyError):
            client.create_user({})

    @patch("tahoe_auth0.api_client.helpers.get_auth0_domain")
    @patch.object(Auth0ApiClient, "_get_access_token")
    def test_create_user_no_username(
        self, mock_get_access_token, mock_get_auth0_domain
    ):
        client = Auth0ApiClient()
        with self.assertRaises(KeyError):
            client.create_user({"name": "Ahmed Jazzar"})

    @patch("tahoe_auth0.api_client.helpers.get_auth0_domain")
    @patch.object(Auth0ApiClient, "_get_access_token")
    def test_create_user_no_email(self, mock_get_access_token, mock_get_auth0_domain):
        client = Auth0ApiClient()
        with self.assertRaises(KeyError):
            client.create_user(
                {
                    "name": "Ahmed Jazzar",
                    "username": "ahmedjazzar",
                }
            )

    @patch("tahoe_auth0.api_client.helpers.get_auth0_domain")
    @patch.object(Auth0ApiClient, "_get_access_token")
    def test_create_user_no_password(
        self, mock_get_access_token, mock_get_auth0_domain
    ):
        client = Auth0ApiClient()
        with self.assertRaises(KeyError):
            client.create_user(
                {
                    "name": "Ahmed Jazzar",
                    "username": "ahmedjazzar",
                    "email": "ahmed@appsembler.com",
                }
            )

    @patch("tahoe_auth0.api_client.requests.post")
    @patch("tahoe_auth0.api_client.helpers.get_auth0_domain")
    @patch.object(Auth0ApiClient, "_get_access_token")
    @patch.object(Auth0ApiClient, "get_connection")
    def test_create_user(
        self,
        mock_get_connection,
        mock_get_access_token,
        mock_get_auth0_domain,
        mock_post,
    ):
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
        )

    @patch("tahoe_auth0.api_client.requests.get")
    @patch("tahoe_auth0.api_client.helpers.get_auth0_domain")
    @patch("tahoe_auth0.api_client.helpers.build_auth0_query")
    @patch.object(Auth0ApiClient, "_get_access_token")
    def test_get_user(
        self,
        mock_get_access_token,
        mock_build_auth0_query,
        mock_get_auth0_domain,
        mock_get,
    ):
        client = Auth0ApiClient()

        query = "test"
        url = client.users_url + "?q={}".format(query)
        mock_build_auth0_query.return_value = query

        user = client.get_user("ahmed@appsembler.com")
        self.assertIsInstance(user, dict)

        mock_get.assert_called_with(url, headers=client.api_headers)
