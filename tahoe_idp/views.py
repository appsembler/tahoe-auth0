import json

from django.http import JsonResponse
from django.shortcuts import redirect
from django.views import View
from django.views.generic import TemplateView
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


# TODO: shadinaif: Restore this view after refactoring it by reading site domain from URL
# TODO: or maybe moving the view to edx-platform
# class StudioWelcomeRedirectAPIView(View):
#     def get(self, request):
#         response = redirect('{scheme}://{studio_base}/welcome/{short_name}/'.format(
#             scheme=request.scheme,
#             studio_base=settings.CMS_BASE,
#             short_name=get_current_organization(request=request).short_name
#         ), permanent=False)
#         return response


class StudioLoginAPIView(View):
    def get(self, request, org_short_name):
        # organization = Organization.objects.get(short_name=org_short_name)
        # studio_site_uuid = get_uuid_by_organization(organization)
        # TODO: shadinaif, fix this view
        return redirect('/auth/login/tahoe-idp/?auth_entry=login', permanent=False)
