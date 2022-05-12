from datetime import timedelta
from uuid import uuid4

from django.conf import settings as djsettings
from django.http import HttpRequest
from django.utils import timezone
from django.utils.crypto import get_random_string
from tahoe_idp import magiclink_settings as settings
from tahoe_idp.magiclink_utils import get_client_ip, get_url_path
from tahoe_idp.models import MagicLink, MagicLinkError


def create_magiclink(
    email: str,
    request: HttpRequest,
    redirect_url: str = '',
) -> MagicLink:
    if settings.EMAIL_IGNORE_CASE:
        email = email.lower()

    limit = timezone.now() - timedelta(seconds=settings.LOGIN_REQUEST_TIME_LIMIT)  # NOQA: E501
    over_limit = MagicLink.objects.filter(email=email, created__gte=limit)
    if over_limit:
        raise MagicLinkError('Too many magic login requests')

    if settings.ONE_TOKEN_PER_USER:
        magic_links = MagicLink.objects.filter(email=email, disabled=False)
        magic_links.update(disabled=True)

    if not redirect_url:
        redirect_url = get_url_path(djsettings.LOGIN_REDIRECT_URL)

    client_ip = None
    if settings.REQUIRE_SAME_IP:
        client_ip = get_client_ip(request)
        if client_ip and settings.ANONYMIZE_IP:
            client_ip = client_ip[:client_ip.rfind('.')+1] + '0'

    expiry = timezone.now() + timedelta(seconds=settings.AUTH_TIMEOUT)
    magic_link = MagicLink.objects.create(
        email=email,
        token=get_random_string(length=settings.TOKEN_LENGTH),
        expiry=expiry,
        redirect_url=redirect_url,
        cookie_value=str(uuid4()),
        ip_address=client_ip,
    )
    return magic_link
