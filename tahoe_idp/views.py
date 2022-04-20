import json

from django.http import Http404, JsonResponse
from django.shortcuts import redirect
from django.conf import settings
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView

from organizations.models import Organization
from site_config_client.openedx import api as config_api

from tahoe_idp.api_client import Auth0ApiClient
from tahoe_idp.api import get_studio_site, save_studio_site_uuid_in_session
from tahoe_idp.helpers import get_lms_login_url
from tahoe_sites.api import get_current_organization, get_organization_by_site, get_uuid_by_organization


class RegistrationView(TemplateView):
    template_name = "tahoe_idp/register.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["organization_name"] = config_api.get_setting_value("PLATFORM_NAME")
        return context


class RegistrationAPIView(View):
    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(RegistrationAPIView, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        client = Auth0ApiClient()

        data = json.loads(request.body.decode("utf-8"))
        resp = client.create_user(data)

        return JsonResponse(resp.json(), status=resp.status_code)


class StudioWelcomeRedirectAPIView(View):
    def get(self, request):
        response = redirect('{scheme}://{studio_base}/welcome/{short_name}/'.format(
            scheme=request.scheme,
            studio_base=settings.CMS_BASE,
            short_name=get_current_organization(request=request).short_name
        ), permanent=False)
        return response


class StudioLoginAPIView(View):
    def get(self, request, org_short_name):
        organization = Organization.objects.get(short_name=org_short_name)
        studio_site_uuid = get_uuid_by_organization(organization)

        if save_studio_site_uuid_in_session(studio_site_uuid=studio_site_uuid) == studio_site_uuid:
            return redirect('/auth/login/tahoe-idp/?auth_entry=login', permanent=False)
        else:
            raise Http404


class NoStudioAccessView(TemplateView):
    template_name = "tahoe_idp/no_studio_access.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        site = get_studio_site()
        context["organization_name"] = get_organization_by_site(site=site).name
        context["lms_url"] = get_lms_login_url()
        return context
