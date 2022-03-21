"""
Auth0 client to communicate with Auth0
"""
import logging

import requests

from openedx.core.djangoapps.appsembler.sites.utils import get_current_organization
from tahoe_auth0 import helpers

logger = logging.getLogger(__name__)


class Auth0ApiClient:
    def __init__(self, request_timeout=10):
        self.request_timeout = request_timeout
        self.domain = helpers.get_auth0_domain()
        self.access_token = self._get_access_token()

    @property
    def token_url(self):
        return "https://{}/oauth/token".format(self.domain)

    @property
    def organization_url(self):
        """
        Returns Auth0's organizations url path, customized for the current
        organization name.
        """
        organization = get_current_organization()

        return "https://{}/api/v2/organizations/name/{}".format(
            self.domain, organization.short_name
        )

    @property
    def users_url(self):
        return "https://{}/api/v2/users".format(self.domain)

    @property
    def change_password_via_reset_url(self):
        # This API uses the legacy password reset call, because api/v2 don't provide a way to reset yet.
        return "https://{}/dbconnections/change_password".format(self.domain)

    @property
    def api_headers(self):
        """
        A common place to set Auth0 API headers.
        """
        return {
            "Content-Type": "application/json",
            "authorization": "Bearer {}".format(self.access_token),
        }

    @property
    def api_identifier(self):
        return "https://{}/api/v2/".format(self.domain)

    @property
    def organization_id(self):
        return self._get_auth0_organization_id()

    def get_connection(self):
        """
        Return the organization connection. The connection name is destructed
        from Auth0 organization ID.
        In Auth0, the organization ID is consists of two parts:
            `org_<unique str>`
        The connection ID is going to be con-<unique str> since Auth0
        doesn't accept `_` in the connection name.
        """
        full_id = self.organization_id
        try:
            org_id = full_id.split("_")[1]
        except IndexError:
            raise ValueError(
                "Unexpected value received for organization_id: {}".format(full_id)
            )

        return "con-{}".format(org_id)

    def change_password_via_reset_for_db_connection(self, email):
        """
        Start password reset for a specific email via /dbconnections/change_password .
        """
        connection = self.get_connection()

        logger.debug("Starting password reset for user %s in connection: %s", email, connection)

        client_id, _client_secret = helpers.get_client_info()
        resp = requests.post(
            self.change_password_via_reset_url,
            json={
                "client_id": client_id,
                "email": email,
                "connection": connection,
            },
            timeout=self.request_timeout,
        )
        logger.info("Response received from password reset api: %s", resp.text)

        resp.raise_for_status()

        return resp

    def update_user(self, auth0_user_id, properties):
        """
        Update Auth0 user properties via PATCH /api/v2/users/.

        See: https://auth0.com/docs/api/management/v2#!/Users/patch_users_by_id
        """
        users_api_url = 'https://{domain}/api/v2/users/{user_id}'.format(
            domain=self.domain,
            user_id=auth0_user_id,
        )

        connection = self.get_connection()

        logger.debug("Updating properties of user %s in connection: %s", auth0_user_id, connection)

        client_id, _client_secret = helpers.get_client_info()
        resp = requests.patch(
            users_api_url,
            json={
                "client_id": client_id,
                "connection": connection,
                **properties,
            },
            headers=self.api_headers,
            timeout=self.request_timeout,
        )
        logger.info("Response received from update user api: %s", resp.text)

        resp.raise_for_status()

        return resp

    def _get_access_token(self):
        """
        Generates an access token token responsible for fetching the
        organizations' data.
        Might not be needed if we decide to store the Auth0 organization ID in our
        `edx-organizations` app.

        We will return a short-living JWT access token that will be used to get needed
        data from Auth0.
        """

        client_id, client_secret = helpers.get_client_info()
        headers = {"content-type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "audience": self.api_identifier,
        }

        logger.debug("Fetching an access token for Auth0")
        r = requests.post(
            self.token_url,
            headers=headers,
            data=data,
            timeout=self.request_timeout,
        )
        r.raise_for_status()

        data = r.json()
        return data["access_token"]

    def _get_auth0_organization_id(self):
        """
        Sends an API request to Auth0 to get the organization details. Needed to sign
        the user in the current organization.
        """
        resp = requests.get(
            self.organization_url,
            headers=self.api_headers,
            timeout=self.request_timeout,
        )

        logger.info(
            "Response received from Auth0 organization API: {}".format(resp.text)
        )
        resp.raise_for_status()

        data = resp.json()
        return data["id"]

    def create_user(self, data):
        """
        Responsible for creating a user in Auth0. Given data must contain the
        following fields:
            - name
            - username
            - email
            - password
        Any extra values you specify in the give `data` will be passed to
        the `user_metadata` field in Auth0 User object.
        """
        name = data.pop("name")
        username = data.pop("username")
        email = data.pop("email")
        password = data.pop("password")

        connection = self.get_connection()

        logger.debug("Creating user {} in connection: {}".format(username, connection))
        resp = requests.post(
            self.users_url,
            headers=self.api_headers,
            json={
                "name": name,
                "username": username,
                "email": email,
                "password": password,
                "email_verified": False,
                "verify_email": True,
                "connection": connection,
                "user_metadata": {
                    "extra_registration_params": data,
                },
            },
            timeout=self.request_timeout,
        )
        logger.info(
            "Response received from Auth0 create user API: {}".format(resp.text)
        )
        resp.raise_for_status()

        return resp

    def get_user(self, email):
        """
        Responsible for fetching user details from Auth0, we mainly use it
        to retrieve users' usernames from a specific connection.
        The way Auth0 handles this API call is returning a search result of a query
        string we pass in the parameters. Since we are searching for a single user,
        we're only expecting one result, if the result is not found we will return
        an empty object.

        A returned object has the following structure
        {
            'name': 'Ahmed Jazzar',
            'last_ip': '107.88.123.45',
            'created_at': '2021-10-02T23:22:15.894Z',
            'user_id': 'auth0|21341jnkjn1k2n3412k31',
            'picture': 'https://s.gravatar.com/avatar/aj.png',
            'last_login': '2021-10-02T23:22:22.847Z',
            'user_metadata': {
                'extra_arg': 'some value',
                'another_arg': 'another value'
            },
            'updated_at': '2021-10-02T23:22:22.848Z',
            'identities': [
                {
                    'provider': 'auth0',
                    'user_id': '21341jnkjn1k2n3412k31',
                    'connection': 'con-7ud2JmLH4vB35mh0',
                    'isSocial': False
                }
            ],
            'logins_count': 14,
            'email': 'ahmed+mw6wbi5mjxjfpmk@appsembler.com',
            'username': 'mw6wbi5mjxjfpmk',
            'nickname': 'ahmed+mw6wbi5mjxjfpmk',
            'email_verified': False
        }
        """
        query = {
            "email": email,
            "identities.connection": self.get_connection(),
        }
        url = self.users_url + "?q={}".format(helpers.build_auth0_query(**query))

        resp = requests.get(
            url,
            headers=self.api_headers,
            timeout=self.request_timeout,
        )
        resp.raise_for_status()

        return resp.json()[0] if len(resp.json()) > 0 else {}
