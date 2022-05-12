"""locallibrary URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from .magiclink_urls import no_login, needs_login, CustomLoginVerify

urlpatterns = [
    path("", include(("tahoe_idp.urls", "tahoe_idp"), namespace="tahoe_idp")),
    # Matches edX Platform
    path("auth/", include("social_django.urls", namespace="social")),
]

urlpatterns += [
    path('no-login/', no_login, name='no_login'),
    path('needs-login/', needs_login, name='needs_login'),
    path('custom-login-verify/', CustomLoginVerify.as_view(), name='custom_login_verify'),  # NOQA: E501
    # path('auth/', include('magiclink.urls', namespace='magiclink')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
