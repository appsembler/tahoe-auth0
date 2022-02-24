"""
Permissions constants and utils for the tahoe-auth0 backend.
"""


AUTH0_ORG_ADMIN_ROLE = 'Admin'
AUTH0_STUDIO_ROLE = 'Staff'
AUTH0_DEFAULT_ROLE = 'Learner'


def is_organization_admin(role):
    """
    Checks if organization admin, which grants admin rights and API access.
    """
    return role == AUTH0_ORG_ADMIN_ROLE


def is_organization_staff(role):
    """
    Check if the role has Staff access which grants access to Open edX Studio.
    """
    return role == AUTH0_STUDIO_ROLE or is_organization_admin(role)


def get_role_with_default(app_metadata):
    """
    Helper to get role from `app_metadata` and default to Learner.
    """
    return app_metadata.get('role', AUTH0_DEFAULT_ROLE)
