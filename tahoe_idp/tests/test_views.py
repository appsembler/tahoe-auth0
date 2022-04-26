import json
from unittest.mock import patch

from django.test import Client, TestCase
from django.urls import reverse
from requests import Response

from site_config_client.openedx.test_helpers import override_site_config

from tahoe_idp.api_client import FusionAuthApiClient
from tahoe_idp.views import RegistrationView


class TestRegistrationView(TestCase):
    def setUp(self) -> None:
        self.view = RegistrationView()

    @override_site_config("setting", PLATFORM_NAME="My Platform")
    def test_get_context_data(self):
        context = self.view.get_context_data()
        self.assertIn("organization_name", context)
        self.assertEqual(context["organization_name"], "My Platform")


class TestRegistrationAPIView(TestCase):
    def setUp(self) -> None:
        self.client = Client()

    def test_get(self):
        """
        Method shouldn't be allowed
        """
        response = self.client.get(reverse("tahoe_idp:register_api"))
        self.assertEqual(response.status_code, 405)

    @patch("tahoe_idp.api_client.helpers.get_idp_base_url")
    @patch.object(FusionAuthApiClient, "_get_access_token")
    @patch.object(FusionAuthApiClient, "create_user")
    def test_post(self, mock_create_user, mock_get_access_token, mock_get_idp_base_url):
        mock_create_user.return_value = create_mocked_response()

        data = {"fid": 43, "bid": 20}
        response = self.client.post(
            reverse("tahoe_idp:register_api"),
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
