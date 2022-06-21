from datetime import timedelta
import logging

from django.conf import settings
from django.http import HttpRequest
from django.utils import timezone
from django.utils.crypto import get_random_string
from tahoe_idp.helpers import import_from_path
from tahoe_idp.models import MagicLink, MagicLinkError

log = logging.getLogger(__name__)


def create_magiclink(
    username: str,
    request: HttpRequest,
    redirect_url: str = None,
) -> MagicLink:
    limit = timezone.now() - timedelta(seconds=settings.MAGICLINK_LOGIN_REQUEST_TIME_LIMIT)  # NOQA: E501
    over_limit = MagicLink.objects.filter(username=username, created_on__gte=limit)
    if over_limit:
        raise MagicLinkError('Too many magic login requests')

    # Only the last magic link is usable per user
    MagicLink.objects.filter(username=username, used=False).update(used=True)

    expiry = timezone.now() + timedelta(seconds=settings.MAGICLINK_AUTH_TIMEOUT)
    magic_link = MagicLink.objects.create(
        username=username,
        token=get_random_string(length=settings.MAGICLINK_TOKEN_LENGTH),
        expiry=expiry,
        redirect_url=redirect_url,
        created_on=timezone.now(),
    )
    return magic_link


def is_studio_allowed_for_user(user):
    """
    Check if the given user is permitted to log into studio or not. Use an external helper method
    set in MAGICLINK_STUDIO_PERMISSION_METHOD

    * If there is no method set; the helper will check for is_staff and is_superuser permissions
    * If MAGICLINK_STUDIO_PERMISSION_METHOD is set but failed to be loaded for any reason; the helper
        will return <False> silently

    :param user:
    :return: <True> if allowed, <False> otherwise
    """
    if not settings.MAGICLINK_STUDIO_PERMISSION_METHOD:
        return user and (user.is_staff or user.is_superuser)

    try:
        external_method = import_from_path(settings.MAGICLINK_STUDIO_PERMISSION_METHOD)
        result = external_method(user)
    except Exception as err:
        log.warning('tahoue_idp.is_studio_allowed_for_user failed for user {username}: {details}'.format(
            username=user.username,
            details=str(err))
        )
        result = False

    return result
