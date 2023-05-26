"""
Constants for the tahoe_idp package.
"""

BACKEND_NAME = 'tahoe-idp'

USER_FIELDS_TO_SYNC_OPENEDX_TO_IDP = {
    'first_name': 'firstName',  # User
    'last_name':  'lastName',  # User
    # 'email': We don't sync on User save().  Instead, sync on confirmation of email change.
    'name': 'fullName',  # UserProfile
    # TODO:  Consider updating user.preferredLanguages from UserPreference model save
}
