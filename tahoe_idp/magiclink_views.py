import logging

from django.contrib.auth import authenticate, get_user_model, login
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.generic import TemplateView


from tahoe_idp import magiclink_settings as settings

from tahoe_idp.models import MagicLink, MagicLinkError
from tahoe_idp.magiclink_utils import get_url_path

User = get_user_model()
log = logging.getLogger(__name__)


@method_decorator(never_cache, name='dispatch')
class LoginVerify(TemplateView):
    template_name = settings.LOGIN_FAILED_TEMPLATE_NAME

    def get(self, request, *args, **kwargs):
        token = request.GET.get('token')
        email = request.GET.get('email')
        user = authenticate(request, token=token, email=email)
        if not user:
            if settings.LOGIN_FAILED_REDIRECT:
                redirect_url = get_url_path(settings.LOGIN_FAILED_REDIRECT)
                return HttpResponseRedirect(redirect_url)

            if not settings.LOGIN_FAILED_TEMPLATE_NAME:
                raise Http404()

            context = self.get_context_data(**kwargs)

            try:
                magiclink = MagicLink.objects.get(token=token)
            except MagicLink.DoesNotExist:
                error = 'A magic link with that token could not be found'
                context['login_error'] = error
                return self.render_to_response(context)

            try:
                magiclink.validate(request, email)
            except MagicLinkError as error:
                context['login_error'] = str(error)

            return self.render_to_response(context)

        login(request, user)
        log.info('Login successful for {email}'.format(email=email))

        response = self.login_complete_action()

        if settings.REQUIRE_SAME_BROWSER:
            magiclink = MagicLink.objects.get(token=token)
            cookie_name = 'magiclink{pk}'.format(pk=magiclink.pk)
            response.delete_cookie(cookie_name, magiclink.cookie_value)

        return response

    def login_complete_action(self) -> HttpResponse:
        token = self.request.GET.get('token')
        magiclink = MagicLink.objects.get(token=token)
        return HttpResponseRedirect(magiclink.redirect_url)
