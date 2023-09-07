from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.views.generic import TemplateView

from proj import views
from users.views import FakeSocialSignup, FakeConfirmEmailView
from paypal.standard.ipn import views as paypal_views

urlpatterns = [
    path("admin", admin.site.urls),
    # path("fake/accounts/social/signup", FakeSocialSignup.as_view()),
    # path("fake/accounts/confirm-email", FakeConfirmEmailView.as_view()),
    path("accounts/", include("allauth.urls")),
    path("__reload__/", include("django_browser_reload.urls")),
    path("__debug__/", include("debug_toolbar.urls")),
    path('', include('proj.urls')),
    path('paypal/', include('paypal.standard.ipn.urls')),
    path('payment_process/', views.payment_process, name='payment_process'),
    path('payment_done/', TemplateView.as_view(template_name="pets/payment_done.html"),name='payment_done'),
    path('payment_canceled/', TemplateView.as_view(template_name="pets/payment_canceled.html"),name='payment_canceled'),
    path('paypal/ipn/', paypal_views.ipn, name='paypal-ipn'),

]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
