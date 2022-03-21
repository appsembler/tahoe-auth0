"""
External Python API helpers goes here.

### API Contract:
 * Those APIs should be stable and abstract internal model changes.

 * Non-stable and internal APIs they should be placed in the `helpers.py` module instead.

 * The parameters of existing functions should change in a backward compatible way:
   - No parameters should be removed from the function
   - New parameters should have safe defaults
 * For breaking changes, new functions should be created
"""

from .api_client import Auth0ApiClient


def request_password_reset(email):
    """
    Start password reset email for Username|Password Database Connection users.
    """
    auth0_api_client = Auth0ApiClient()
    return auth0_api_client.change_password_via_reset_for_db_connection(email)
