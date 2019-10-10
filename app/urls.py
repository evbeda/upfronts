from django.conf.urls import url
from django.views.generic.base import RedirectView

from app import views


urlpatterns = [
    url(r'^contracts/search/', views.ContractAdd.as_view(), name='contracts-add'),
    url(r'^contracts/update/(?P<pk>[0-9]+)/$', views.ContractUpdate.as_view(), name='contracts-update'),
    url(r'^contracts/save/(?P<contract_id>\w+)/$', views.SaveCaseView.as_view(), name='contracts-save'),
    url(
        r'^contracts/(?P<contract_id>[0-9]+)/installments/$',
        views.InstallmentView.as_view(),
        name='installments-create',
    ),
    url(r'^contracts/installments/$', views.AllInstallmentsView.as_view(), name='all-installments'),
    url(r'^contracts/', views.ContractsTableView.as_view(), name='contracts'),
    url(r'^', RedirectView.as_view(url='/contracts/'), name='redirect-url'),
]
