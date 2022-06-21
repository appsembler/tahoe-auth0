from urllib.parse import urlencode, urljoin

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.http import HttpRequest
from django.urls import reverse
from django.utils import timezone

User = get_user_model()


class MagicLinkError(Exception):
    pass


class MagicLink(models.Model):
    username = models.CharField(max_length=254)
    token = models.TextField()
    expiry = models.DateTimeField()
    redirect_url = models.TextField(null=True)
    used = models.BooleanField(default=False)
    created_on = models.DateTimeField()

    def __str__(self):
        return '{username} - {expiry}'.format(username=self.username, expiry=self.expiry)

    def generate_url(self, request: HttpRequest) -> str:
        url_path = reverse(settings.MAGICLINK_LOGIN_VERIFY_URL)

        params = {
            'token': self.token,
            'username': self.username,
        }
        query = urlencode(params)

        url_path = '{url_path}?{query}'.format(url_path=url_path, query=query)
        scheme = request.is_secure() and 'https' or 'http'
        url = urljoin(
            '{scheme}://{studio_domain}'.format(scheme=scheme, studio_domain=settings.MAGICLINK_STUDIO_DOMAIN),
            url_path
        )
        return url

    def _validation_error(self, error_message):
        self.used = True
        self.save()
        raise MagicLinkError(error_message)

    def get_user_with_validate(
        self,
        request: HttpRequest,
        username: str = '',
    ) -> AbstractUser:
        if self.used:
            raise MagicLinkError('Magic link already used')

        if self.username != username:
            raise MagicLinkError('username does not match')

        if timezone.now() > self.expiry:
            self._validation_error('Magic link has expired')

        user = User.objects.get(username=self.username)

        self.used = True
        self.save()

        return user
