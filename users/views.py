from allauth.socialaccount.forms import SignupForm
from allauth.socialaccount.models import SocialLogin
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.urls import include, path
from django.views.generic.base import TemplateView

User = get_user_model()


class FakeSocialSignup(TemplateView):
    template_name = "socialaccount/signup.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        fake_sociallogin = SocialLogin(user=User.objects.first())
        context["form"] = SignupForm(sociallogin=fake_sociallogin)
        return context


# class ConfirmEmailView(TemplateResponseMixin, LogoutFunctionalityMixin, View):
class FakeConfirmEmailView(TemplateView):
    template_name = "account/email_confirm.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.GET.get("confirmation"):
            context["confirmation"] = dict(
                key="ok", email_address=dict(user="dani", email="dani@hello.com")
            )
        return context
