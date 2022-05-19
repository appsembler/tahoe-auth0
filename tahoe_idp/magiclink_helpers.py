from datetime import timedelta

from django.conf import settings as djsettings
from django.http import HttpRequest
from django.utils import timezone
from django.utils.crypto import get_random_string
from tahoe_idp import magiclink_settings as settings
from tahoe_idp.magiclink_utils import get_url_path
from tahoe_idp.models import MagicLink, MagicLinkError


def create_magiclink(
    username: str,
    request: HttpRequest,
    redirect_url: str = '',
) -> MagicLink:
    limit = timezone.now() - timedelta(seconds=settings.LOGIN_REQUEST_TIME_LIMIT)  # NOQA: E501
    over_limit = MagicLink.objects.filter(username=username, created_on__gte=limit)
    if over_limit:
        raise MagicLinkError('Too many magic login requests')

    if settings.ONE_TOKEN_PER_USER:
        magic_links = MagicLink.objects.filter(username=username, used=False)
        magic_links.update(used=True)

    if not redirect_url:
        redirect_url = get_url_path(djsettings.LOGIN_REDIRECT_URL)

    expiry = timezone.now() + timedelta(seconds=settings.AUTH_TIMEOUT)
    magic_link = MagicLink.objects.create(
        username=username,
        token=get_random_string(length=settings.TOKEN_LENGTH),
        expiry=expiry,
        redirect_url=redirect_url,
        created_on=timezone.now(),
    )
    return magic_link
