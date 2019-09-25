from django.conf.urls import url
from django.views.generic.base import RedirectView
from . import views


urlpatterns = [
    url(r'^installments/', views.InstallmentsTableView.as_view(), name='installments'),
    url(r'^', RedirectView.as_view(url='/installments/'), name='redirect-url'),
]
