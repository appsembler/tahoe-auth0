from datetime import timedelta

from django.conf import settings
from django.http import HttpRequest
from django.utils import timezone
from django.utils.crypto import get_random_string
from tahoe_idp.magiclink_utils import get_url_path
from tahoe_idp.models import MagicLink, MagicLinkError


def create_magiclink(
    username: str,
    request: HttpRequest,
    redirect_url: str = '',
) -> MagicLink:
    limit = timezone.now() - timedelta(seconds=settings.MAGICLINK_LOGIN_REQUEST_TIME_LIMIT)  # NOQA: E501
    over_limit = MagicLink.objects.filter(username=username, created_on__gte=limit)
    if over_limit:
        raise MagicLinkError('Too many magic login requests')

    # Only the last magic link is usable per user
    MagicLink.objects.filter(username=username, used=False).update(used=True)

    if not redirect_url:
        redirect_url = get_url_path(settings.LOGIN_REDIRECT_URL)

    expiry = timezone.now() + timedelta(seconds=settings.MAGICLINK_AUTH_TIMEOUT)
    magic_link = MagicLink.objects.create(
        username=username,
        token=get_random_string(length=settings.MAGICLINK_TOKEN_LENGTH),
        expiry=expiry,
        redirect_url=redirect_url,
        created_on=timezone.now(),
    )
    return magic_link
