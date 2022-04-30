from urllib.parse import urlencode

import json
from django.conf import settings

from django.http import JsonResponse
from django.shortcuts import redirect
from django.views import View
from django.views.generic import TemplateView

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from magiclink.helpers import create_magiclink

from site_config_client.openedx import api as config_api

from tahoe_idp.api_client import Auth0ApiClient



class RegistrationView(TemplateView):
    template_name = "tahoe_idp/register.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["organization_name"] = config_api.get_setting_value("PLATFORM_NAME")
        return context


class RegistrationAPIView(View):
    def post(self, request, *args, **kwargs):
        client = Auth0ApiClient()

        data = json.loads(request.body.decode("utf-8"))
        resp = client.create_user(data)

        return JsonResponse(resp.json(), status=resp.status_code)


class StudioLogin(View):
    @method_decorator(login_required)
    def get(self, request):
        redirect_url = request.get('next', '')
        # is_safe_login_or_logout_redirect(redirect_url)
        email = request.user.email
        magic_link = create_magiclink(email, request, redirect_url=redirect_url)
        url = magic_link.generate_url(request)

        params = {'token': magic_link.token}
        if settings.VERIFY_INCLUDE_EMAIL:
            params['email'] = self.email
        query = urlencode(params)

        url_path = '{url_path}?{query}'.format(
            url_path='http://localhost:18010/auth_link/'
        )
        domain = get_current_site(request).domain
        scheme = request.is_secure() and 'https' or 'http'
        url = urljoin(f'{scheme}://{domain}', url_path)

        studio_url =

        return redirect(url)
