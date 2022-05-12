from django.contrib.auth.decorators import login_required
from django.http.response import HttpResponse, HttpResponseRedirect
from django.urls import include, path, reverse

from tahoe_idp.magiclink_views import LoginVerify


@login_required
def needs_login(request):
    return HttpResponse()


def no_login(request):
    return HttpResponse()


class CustomLoginVerify(LoginVerify):

    def login_complete_action(self) -> HttpResponse:
        url = reverse('no_login')
        return HttpResponseRedirect(url)
