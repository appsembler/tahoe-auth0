from django.conf.urls import url, include
from django.contrib import admin

urlpatterns = [
    url(r"^admin/", admin.site.urls),
    url(r"^", include("tahoe_auth0.urls", namespace="tahoe_auth0")),
]
