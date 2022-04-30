from django.urls import path

from .views import RegistrationAPIView, RegistrationView, StudioLogin

urlpatterns = [
    path("register", RegistrationAPIView.as_view(), name="register_api"),
    path("studio", StudioLogin.as_view(), name="studio_idp_login"),
    # TODO: remove when not necessary
    path("signup", RegistrationView.as_view(), name="register_view"),
]
