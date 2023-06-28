"""
Signal receivers for tahoe-idp Django app.
"""

from django.contrib.auth.models import User

from . import api, constants, helpers


def user_sync_to_idp(sender, instance, **kwargs):
    """
    Sync select User and UserProfile attributes back to the IdP.

    Handles post_save Signals from User, UserProfile

    We want to keep the user record in the IdP up to date with any changes made via
    Account Settings, Django admin, or otherwise.
    """

    # Not necessary to sync if just created.  Already in sync.
    if kwargs['created']:
        return

    if not helpers.is_tahoe_idp_enabled():  # avoid edx-platform test failures
        return

    fields_to_sync = constants.USER_FIELDS_TO_SYNC_OPENEDX_TO_IDP

    user_update_dict = {}

    for field in instance._meta.fields:
        if field.name in fields_to_sync.keys():
            user_update_dict[fields_to_sync[field.name]] = getattr(instance, field.name)

    if user_update_dict:
        user = instance if sender == User else instance.user
        # will raise an Exception from raise_for_status if failure code
        api.update_user(user, {
                'user': user_update_dict
            }
        )
