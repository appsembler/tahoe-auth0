from django.urls import re_path

from tahoe_idp.magiclink_views import LoginVerify, StudioLoginAPIView

urlpatterns = [
    re_path('^verify_login/?$', LoginVerify.as_view(), name='verify_login'),
    re_path('^studio/?$', StudioLoginAPIView.as_view(), name='studio'),
]
