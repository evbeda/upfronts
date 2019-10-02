from django.conf.urls import url
from django.views.generic.base import RedirectView

from app import views


urlpatterns = [
    url(r'^contracts/search/', views.ContractAdd.as_view(), name='contracts-add'),
    url(r'^contracts/update/(?P<pk>[0-9]+)/$', views.ContractUpdate.as_view(), name='contracts-update'),
    url(r'^contracts/save/(?P<contract_id>\w+)/$', views.SaveCaseView.as_view(), name='contracts-save'),
    url(r'^contracts/', views.ContractsTableView.as_view(), name='contracts'),
    url(r'^installments/create/(?P<contract_id>[0-9]+)/$', views.InstallmentView.as_view(), name='installments-create'),
    url(r'^', RedirectView.as_view(url='/contracts/'), name='redirect-url'),
]
