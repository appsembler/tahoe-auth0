from django.urls import path

from tahoe_idp.magiclink_views import LoginVerify, StudioLoginAPIView

urlpatterns = [
    path('login/verify/', LoginVerify.as_view(), name='login_verify'),
    path('studio/', StudioLoginAPIView.as_view(), name='studio'),
]
