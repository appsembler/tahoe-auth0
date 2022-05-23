import logging

from django.contrib.auth import get_user_model
from django.http import HttpRequest

from tahoe_idp.models import MagicLink, MagicLinkError

User = get_user_model()
log = logging.getLogger(__name__)


class MagicLinkBackend:

    def authenticate(  # nosec - disable claim from bandit that a password is hardcoded
        self,
        request: HttpRequest,
        token: str = '',
        username: str = '',
    ):
        log.debug('MagicLink authenticate token: {token} - username: {username}'.format(token=token, username=username))

        if not token:
            log.warning('Token missing from authentication')
            return

        if not username:
            log.warning('username not supplied with token')
            return

        try:
            magiclink = MagicLink.objects.get(token=token)
        except MagicLink.DoesNotExist:
            log.debug('MagicLink with token "{token}" not found'.format(token=token))
            return

        try:
            user = magiclink.get_user_with_validate(request, username)
        except MagicLinkError as error:
            log.debug(error)
            return

        log.info('{username} authenticated via MagicLink'.format(username=user.username))

        return user

    @staticmethod
    def get_user(user_id):
        return User.objects.filter(pk=user_id).first()
