# Tahoe Auth 0 ![https://codecov.io/gh/appsembler/tahoe-auth0](https://codecov.io/gh/appsembler/tahoe-auth0/branch/master/graph/badge.svg)

A package of tools and features for integrating Tahoe with Auth0


## Quickstart

Install Tahoe Auth0
```console
pip install tahoe-auth0
```

Add it to your `INSTALLED_APPS`:

```python
INSTALLED_APPS = (
    ...
    'tahoe_auth0.apps.TahoeAuth0Config',
    ...
)
```

Add Tahoe Auth0's URL patterns:

```python
from tahoe_auth0 import urls as tahoe_auth0_urls


urlpatterns = [
    ...
    url(r'^', include(tahoe_auth0_urls)),
    ...
]
```

## Features

* TODO

## Running Tests
-------------

Does the code actually work?

```console
source <YOURVIRTUALENV>/bin/activate
(myenv) $ pip install -r requirements_test.txt
(myenv) $ tox
```


## Development commands

```console
pip install -r requirements_dev.txt
invoke -l
```
