"""
Permissions constants and utils for the tahoe-idp backend.
"""


IDP_ORG_ADMIN_ROLE = 'Admin'
IDP_STUDIO_ROLE = 'Staff'
IDP_DEFAULT_ROLE = 'Learner'


METADATE_ROLE_FIELD = 'platform_role'


def is_organization_admin(role):
    """
    Checks if organization admin, which grants admin rights and API access.
    """
    return role == IDP_ORG_ADMIN_ROLE


def is_organization_staff(role):
    """
    Check if the role has Staff access which grants access to Open edX Studio.
    """
    return role == IDP_STUDIO_ROLE or is_organization_admin(role)


def get_role_with_default(user_data):
    """
    Helper to get role from `user.data.platform_role` and default to Learner.
    """
    return user_data.get(METADATE_ROLE_FIELD, IDP_DEFAULT_ROLE)
