from django.conf.urls import url
from django.views.generic import TemplateView


app_name = "tahoe_auth0"
urlpatterns = [
    url(r"", TemplateView.as_view(template_name="base.html")),
]
