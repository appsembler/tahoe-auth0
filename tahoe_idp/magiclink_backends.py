import logging

from django.contrib.auth import get_user_model
from django.http import HttpRequest

from tahoe_idp import magiclink_settings as settings
from tahoe_idp.models import MagicLink, MagicLinkError

User = get_user_model()
log = logging.getLogger(__name__)


class MagicLinkBackend():

    def authenticate(  # nosec - disable claim from bandit that a password is hardcoded
        self,
        request: HttpRequest,
        token: str = '',
        email: str = '',
    ):
        log.debug('MagicLink authenticate token: {token} - email: {email}'.format(token=token, email=email))

        if not token:
            log.warning('Token missing from authentication')
            return

        if settings.VERIFY_INCLUDE_EMAIL and not email:
            log.warning('Email address not supplied with token')
            return

        try:
            magiclink = MagicLink.objects.get(token=token)
        except MagicLink.DoesNotExist:
            log.warning('MagicLink with token "{token}" not found'.format(token=token))
            return

        if magiclink.disabled:
            log.warning('MagicLink "{pk}" is disabled'.format(pk=magiclink.pk))
            return

        try:
            user = magiclink.validate(request, email)
        except MagicLinkError as error:
            log.warning(error)
            return

        magiclink.used()
        log.info('{user} authenticated via MagicLink'.format(user=user))
        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return
