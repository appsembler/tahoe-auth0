from django.urls import path

from tahoe_idp.views import RegistrationAPIView, RegistrationView
from tahoe_idp.magiclink_views import LoginVerify

urlpatterns = [
    path("register", RegistrationAPIView.as_view(), name="register_api"),
    # TODO: remove when not necessary
    path("signup", RegistrationView.as_view(), name="register_view"),
]

# Magic link URLs
urlpatterns += [
    # path('login/', Login.as_view(), name='login'),
    # path('login/sent/', LoginSent.as_view(), name='login_sent'),
    # path('signup/', Signup.as_view(), name='signup'),
    path('login/verify/', LoginVerify.as_view(), name='login_verify'),
    # path('logout/', Logout.as_view(), name='logout'),
]
