import json
from unittest.mock import patch

from django.test import Client, TestCase
from django.urls import reverse
from requests import Response

from tahoe_auth0.api_client import Auth0ApiClient
from tahoe_auth0.views import RegistrationView


class TestRegistrationView(TestCase):
    def setUp(self) -> None:
        self.view = RegistrationView()

    @patch("tahoe_auth0.views.get_current_organization")
    def test_get_context_data(self, mock_get_current_organization):
        context = self.view.get_context_data()

        mock_get_current_organization.assert_called_once_with()
        self.assertIn("organization_name", context)
        self.assertEqual(
            context["organization_name"],
            mock_get_current_organization.return_value.name,
        )


class TestRegistrationAPIView(TestCase):
    def setUp(self) -> None:
        self.client = Client()

    def test_get(self):
        """
        Method shouldn't be allowed
        """
        response = self.client.get(reverse("tahoe_auth0:register_api"))
        self.assertEqual(response.status_code, 405)

    @patch("tahoe_auth0.api_client.helpers.get_auth0_domain")
    @patch.object(Auth0ApiClient, "_get_access_token")
    @patch.object(Auth0ApiClient, "create_user")
    def test_post(self, mock_create_user, mock_get_access_token, mock_get_auth0_domain):
        mock_create_user.return_value = create_mocked_response()

        data = {"fid": 43, "bid": 20}
        response = self.client.post(
            reverse("tahoe_auth0:register_api"),
            data=data,
            content_type="application/json",
        )

        mock_create_user.assert_called_once_with(data)
        self.assertEqual(
            response.status_code, mock_create_user.return_value.status_code
        )
        self.assertEqual(
            json.loads(response.content.decode("utf-8")),
            mock_create_user.return_value.json(),
        )


def create_mocked_response(data=None, status_code=200):
    data = data if data else {}
    response = Response()

    response._content = json.dumps(data).encode("utf-8")
    response.status_code = status_code

    return response
