from django.urls import path

from tahoe_idp.views import RegistrationAPIView, RegistrationView

urlpatterns = [
    path("register", RegistrationAPIView.as_view(), name="register_api"),
    # TODO: remove when not necessary
    path("signup", RegistrationView.as_view(), name="register_view"),
]
