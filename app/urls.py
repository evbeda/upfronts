from django.conf.urls import url
from django.views.generic.base import RedirectView

from app import views


urlpatterns = [
    url(r'^contracts/update/(?P<pk>[0-9]+)/$', views.ContractUpdate.as_view(), name='contracts-update'),
    url(r'^contracts/', views.ContractsTableView.as_view(), name='contracts'),
    url(r'^', RedirectView.as_view(url='/contracts/'), name='redirect-url'),
]
