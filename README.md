# Tahoe Auth0 [![TahoeAuth0 Library](https://github.com/appsembler/tahoe-auth0/actions/workflows/tests.yml/badge.svg)](https://github.com/appsembler/tahoe-auth0/actions/workflows/tests.yml) ![Black code style](https://img.shields.io/badge/code%20style-black-000000.svg)

A package of Auth0 user authentication modules designed to work in Open edX.


## Install

### Devstack

We can achieve this using two ways. Both of these methods work in Sultan and
normal Docker setup:

- A quick setup (not persistent).
```console
$ cd /path/to/devstack
$ make lms-shell
$ pip install https://github.com/appsembler/tahoe-auth0
```
- A persistent setup
```python
# TODO: Fill this out
```

## Configure the edX app

### Devstack configurations
In your `edxapp-envs/lms.yml`:

```yaml
FEATURES:
  ...
  AUTH0_DOMAIN: <domain>  # Fetched from Auth0 Site > Settings > Custom Domains
  ENABLE_THIRD_PARTY_AUTH: true
  ...

...
ADDL_INSTALLED_APPS: [
    "tahoe_auth0",
]
THIRD_PARTY_AUTH_BACKENDS: [
    "tahoe_auth0.backend.Auth0"
]
...
```


## Migrate DB

```console
$ cd /path/to/devstack
$ make lms-shell
$ python manage.py lms migrate
```

> Note: You might need to restart your devstack at this point using `make lms-restart`


## Admin Panel Configurations
At this stage, you were able to hook the library with Open edX, to finalize
the setup, you need to add some additional configurations in your LMS admin
panel.

- In your browser, head to [http://localhost:18000/admin]()
- Go to Third Party Auth > Provider Configuration (OAuth) ([http://localhost:18000/admin/third_party_auth/oauth2providerconfig/]()).
- Click **Add Provider Configuration**.
  - Check `Enabled`.
  - Check `Visible`.
  - For the `Name` field. Let's call it `Auth0`.
  - Uncheck `Skip Email Verification`.
  - Insert `tahoe-auth0` in the `Backend Name` field.
  - Insert your Auth0 `Client ID` and `Client Secret`.
  - In `Other Settings`, insert the following:
    ```json
    {"SCOPE": ["openid profile email"]}
    ```

> Using these settings will make sure edX Platform can read the user's email,
> profile from Auth0.


## Auth0's Django tutorial
The implementation in this project was based on the Auth0's Django tutorial here:
[https://auth0.com/docs/quickstart/webapp/django/01-login#configure-auth0](https://auth0.com/docs/quickstart/webapp/django/01-login#configure-auth0)
