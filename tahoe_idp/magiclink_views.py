import logging

from django.conf import settings as django_settings
from django.contrib.auth import authenticate, get_user_model, login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.generic import TemplateView, View

from tahoe_idp import magiclink_settings
from tahoe_idp.magiclink_helpers import create_magiclink
from tahoe_idp.magiclink_utils import get_url_path
from tahoe_idp.models import MagicLink

User = get_user_model()
log = logging.getLogger(__name__)


@method_decorator(never_cache, name='dispatch')
class LoginVerify(TemplateView):
    def get(self, request, *args, **kwargs):
        token = request.GET['token']
        username = request.GET['username']
        user = authenticate(request, token=token, username=username)
        if not user:
            redirect_url = get_url_path(magiclink_settings.LOGIN_FAILED_REDIRECT)
            return HttpResponseRedirect(redirect_url)

        login(request, user)
        log.info('Login successful for {username}'.format(username=username))

        response = self.login_complete_action()

        return response

    def login_complete_action(self) -> HttpResponseRedirect:
        token = self.request.GET.get('token')
        magiclink = MagicLink.objects.get(token=token)
        return HttpResponseRedirect(magiclink.redirect_url or django_settings.LOGIN_REDIRECT_URL)


class StudioLoginAPIView(View):
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(StudioLoginAPIView, self).dispatch(request, *args, **kwargs)

    def get(self, request):
        username = request.user.username
        next_url = request.GET.get('next') or '/home'

        magic_link = create_magiclink(username=username, request=request, redirect_url=next_url)

        url = magic_link.generate_url(request)
        return redirect(url, permanent=False)
