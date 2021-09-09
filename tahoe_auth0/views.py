import json

from django.http import JsonResponse
from django.views import View
from django.views.generic import TemplateView

from openedx.core.djangoapps.appsembler.sites.utils import get_current_organization
from tahoe_auth0.api_client import Auth0ApiClient


class RegistrationView(TemplateView):
    template_name = "register.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        organization = get_current_organization()
        context["organization_name"] = organization.name
        return context


class RegistrationAPIView(View):
    def post(self, request, *args, **kwargs):
        client = Auth0ApiClient()

        data = json.loads(request.body.decode("utf-8"))
        resp = client.create_user(data)

        return JsonResponse(resp.json(), status=resp.status_code)
