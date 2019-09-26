from django.conf.urls import url
from django.views.generic.base import RedirectView
from . import views


urlpatterns = [
    url(r'^installments/update/(?P<pk>[0-9]+)/$', views.InstallmentUpdate.as_view(), name='installments-update'),
    url(r'^installments/', views.InstallmentsTableView.as_view(), name='installments'),
    url(r'^', RedirectView.as_view(url='/installments/'), name='redirect-url'),
]
