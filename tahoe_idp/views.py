import json

from django.http import JsonResponse
from django.views import View
from django.views.generic import TemplateView

from site_config_client.openedx import api as config_api

from tahoe_idp.api_client import FusionAuthApiClient


class RegistrationView(TemplateView):
    template_name = "tahoe_idp/register.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["organization_name"] = config_api.get_setting_value("PLATFORM_NAME")
        return context


class RegistrationAPIView(View):
    def post(self, request, *args, **kwargs):
        client = FusionAuthApiClient()

        data = json.loads(request.body.decode("utf-8"))
        resp = client.create_user(data)

        return JsonResponse(resp.json(), status=resp.status_code)
