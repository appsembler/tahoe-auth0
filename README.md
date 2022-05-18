# Tahoe Identity Provider [![CI](https://github.com/appsembler/tahoe-idp/actions/workflows/tests.yml/badge.svg)](https://github.com/appsembler/tahoe-idp/actions/workflows/tests.yml) ![Black code style](https://img.shields.io/badge/code%20style-black-000000.svg)

A package of IdP user authentication modules designed to work in Open edX.


## README NEEDS UPDATE
The readme is obsolete because this package is now using FusionAuth instead of Auth0.


## 0. Prerequisites
To be able to use this library, you need to have the following
- An Auth0 [Tenant](https://auth0.com/docs/get-started/create-tenants).
- An Auth0 [API](https://auth0.com/docs/get-started/set-up-apis)
- An Auth0 [Machine to Machine](https://auth0.com/docs/get-started/create-apps/machine-to-machine-apps) application.
- At least one organization.
- One custom connection.

### 0.1. Configuring the API
We need to register an API to perform user registration and to communicate with
Auth0 organizations.

Your API must have the following permissions:
  - `read:users`
  - `update:users`
  - `delete:users`
  - `create:users`
  - `read:user_idp_tokens`
  - `read:organizations`
  - `create:organization_invitations`

### 0.2. Configuring the Machine to Machine application
We need to integrate Auth0 with a machine-to-machine (M2M) application. This library
will use this Machine to Machine application to be able to communicate with
the API we configured above for two purposes:
  - Registering users.
  - Reading organizations and hook them with edx-platform.

This application doesn't require extra configuration.

> **NOTE**
>
> The Client ID and Secret of this application are going to be added to
> `TAHOE_IDP_CONFIGS` settings.

### 0.3. Hooking the Machine to Machine application with the API
Go to the settings page of your API. Click **Machine to Machine Applications** tab and:
  - Authorize your Machine to Machine application created in the previous step to use the API.
  - Allow this Machine to Machine application to use all the permission specified above from this API.

### 0.4. Create Regular Web Application
This application is the primary application our edX platoform is going to use
to authenticate users.

- For the **Allowed Callback URLs** use something similar to this [http://*.devstack.site:18000/auth/complete/tahoe-idp/]() or configure yours.
- For the **Allowed Logout URLs** use something similar to this [http://localhost:18000/]() or configure yours.

> **NOTE**
>
> The Client ID and Secret of this application are going to be used in the
> edx-platform Admin settings.

### 0.5. Configure the Organization
Each organization is going to be mapped to a single edx-platform organization.
- The Auth0 organization ID (Similar to `org_1Ab2Cd3`) should be saved into `admin` config in Site Configuration.  
- Save the organization ID to create a connection later.

### 0.6. Configure the Connection
Go to your tenant's _Authentication > Database_ section, and create a custom
connection for your organization.
- Connection name must be `con-{org_id}` (For example `con-1Ab2Cd3`).
- Save the connection ID in `IDP_CONNECTION_ID` the `admin` config in Site Configuration.
- Set `Requires Username` to true and its maximum length to 30 to match current edX setup.
- In the Applications tab of your connection; Allow your `Regular Web Application` and `Machine to Machine`.
- Go back to the settings page of the organization you just created, click `Connection`, then:
  - Enable the connection you created above.
  - Make sure to "Enable Auto-Membership"

You should be all set now.

## 1. Install

### 1.1. Production
To use this library in production, add the following to you Ansible deployment:
```yaml
EDXAPP_EXTRA_REQUIREMENTS:
  - name: 'git+https://github.com/appsembler/tahoe-idp.git#egg=tahoe-idp'
```

### 1.2. Devstack

We can achieve this using two ways. Both of these methods work in Sultan and
normal Docker setup:

#### 1.2.1. A quick setup (not persistent).
```shell
cd /path/to/devstack
make lms-shell
pip install git+https://github.com/appsembler/tahoe-idp
```
#### 1.2.2. Sultan
In your sultan in configurations file (`configs/.configs.<username>`), append
the repo path to `EDXAPP_EXTRA_REQUIREMENTS`:

```shell
EDXAPP_EXTRA_REQUIREMENTS="...,https://github.com/appsembler/tahoe-idp.git,..."
```

Then on your host machine run the following command:
```shell
sultan instance reconfigure
```

> **NOTE**
>
> Using this method requires you to manually install `python-jose==3.2.0` in LMS shell
> ```
> $ make lms-shell
> $ pip install python-jose==3.2.0  # version 3.3.0 won't work on python 3.5
> ```

## 2. Configure the edX app
This package is following edx-platform plugin architecture. Check [plugins#0b4072b](https://github.com/edx/edx-django-utils/tree/0b4072bea3c4610d654a670b3047a7391deaa69f/edx_django_utils/plugins) documentation for more info on plugins.

In your `edxapp-envs/lms.yml`:

```yaml
EDXAPP_EXTRA_REQUIREMENTS:
  - name: "tahoe-idp"

FEATURES:
    ...
    ENABLE_TAHOE_IDP: true
    ...

THIRD_PARTY_AUTH_BACKENDS: [
    "tahoe_idp.backend.TahoeIdpOAuth2"
]

TAHOE_IDP_CONFIGS:
    DOMAIN: <domain>
    API_CLIENT_ID: <client id>
    API_CLIENT_SECRET: <client secret>
...
```

#### Settings Description
- `THIRD_PARTY_AUTH_BACKENDS`: Tell Django to use this backend when attempting to authenticate a user.
- `FEATURES`: edX platform features settings
  - `ENABLE_TAHOE_IDP`: A switch to enable/disable this plugin. We will use this value if and only if `ENABLE_TAHOE_IDP` is not defined in Site Configurations.
- `TAHOE_IDP_CONFIGS` A parent node of Auth0 settings. If not configured while the plugin is enabled, we will raise an error.
  - `DOMAIN`: Your Auth0 Domain assigned to you when creating the tenant, or your configured [Custom Domain](https://auth0.com/docs/brand-and-customize/custom-domains).
  - `API_CLIENT_ID`: The client ID of your Auth0 _Machine to Machine_ app. Fetched from `Auth0 Site > Applications > Applications > Your Machine to Machine App > Client ID`
  - `API_CLIENT_SECRET`: The client Secret of your Auth0 _Machine to Machine_ app. Fetched from `Auth0 Site > Applications > Applications > Your Machine to Machine App > Client Secret`

Now run `make dev.up`, or `sultan devstack up` if you're using Sultan.

> **NOTE**
>
> You might need to restart your devstack at this point using `make lms-restart`

## 3. Admin Panel Configurations
At this stage, you were able to hook the library with Open edX, to finalize
the setup, you need to add some additional configurations in your LMS admin
panel.

- In your browser, head to [http://localhost:18000/admin]()
- Go to [THIRD-PARTY AUTHENTICATION > Provider Configuration (OAuth)](http://localhost:18000/admin/third_party_auth/oauth2providerconfig/).
- Click **Add Provider Configuration**.
  - Check `Enabled`.
  - For the `Name` field, we're going to call it `Auth0`.
  - Check `Skip registration form` (This library will handle this).
  - Check `Skip email verification` (Auth0 will handle this).
  - Check `Visible`.
  - Choose `tahoe-idp` in the `Backend Name` field.
  - Insert your Auth0 _Regular Web Application_'s `Client ID` and `Client Secret`.
  - In `Other Settings`, insert the following:
    ```json
    {"SCOPE": ["openid profile email"]}
    ```

> **NOTE**
>
> Using these scopes will make sure edX Platform can read the user's email
> and profile from Auth0.


## 4. Auth0's Django tutorial
The implementation in this project was based on the Auth0's Django tutorial here:
[https://auth0.com/docs/quickstart/webapp/django/01-login#configure-auth0](https://auth0.com/docs/quickstart/webapp/django/01-login#configure-auth0)
