from django.conf.urls import url
from django.views.generic.base import RedirectView

from app import views


urlpatterns = [
    url(r'^contracts/search/', views.ContractAdd.as_view(), name='contracts-add'),
    url(r'^contracts/update/(?P<pk>[0-9]+)/$', views.ContractUpdate.as_view(), name='contracts-update'),
    url(r'^contracts/(?P<pk>[0-9]+)/detail/$', views.DetailContractView.as_view(), name='contracts-detail'),
    url(r'^contracts/save/(?P<contract_id>\w+)/$', views.SaveCaseView.as_view(), name='contracts-save'),
    url(
        r'^contracts/(?P<contract_id>[0-9]+)/installments/$',
        views.InstallmentView.as_view(),
        name='installments-create',
    ),
    url(
        r'^contracts/(?P<contract_id>[0-9]+)/installments/update/(?P<pk>[0-9]+)/$',
        views.InstallmentUpdate.as_view(),
        name='installments-update',
    ),
    url(
        r'^contracts/(?P<contract_id>[0-9]+)/installments/delete/(?P<pk>[0-9]+)/$',
        views.InstallmentDelete.as_view(),
        name='installments-delete',
    ),
    url(
        r'^contracts/(?P<contract_id>[0-9]+)/installments/(?P<installment_id>[0-9]+)/conditions/$',
        views.ConditionView.as_view(),
        name='conditions',
    ),
    url(
        r'^contracts/(?P<contract_id>[0-9]+)/installments/(?P<installment_id>[0-9]+)'
        '/conditions/(?P<condition_id>[0-9]+)/toggle/$',
        views.ToggleConditionView.as_view(),
        name='toggle-condition',
    ),
    url(
        r'^contracts/(?P<contract_id>[0-9]+)/events/$',
        views.CreateEvent.as_view(),
        name='events-create',
    ),
    url(
        r'^contracts/(?P<contract_id>[0-9]+)/events/(?P<event_id>[0-9]+)/$',
        views.DeleteEvent.as_view(),
        name='events-delete',
    ),
    url(
        r'^contracts/(?P<contract_id>[0-9]+)/installments/(?P<installment_id>[0-9]+)'
        '/conditions/(?P<condition_id>[0-9]+)/delete-file/$',
        views.DeleteUploadedFileCondition.as_view(),
        name='delete-uploaded-file',
    ),
    url(
        r'^contracts/(?P<contract_id>[0-9]+)/installments/(?P<installment_id>[0-9]+)'
        '/conditions/(?P<condition_id>[0-9]+)/backup-proof/$',
        views.ConditionBackupProofView.as_view(),
        name='condition_backup_proof',
    ),
    url(
        r'^contracts/(?P<contract_id>[0-9]+)/installments/(?P<installment_id>[0-9]+)'
        '/conditions/(?P<condition_id>[0-9]+)/delete-condition/$',
        views.DeleteInstallmentCondition.as_view(),
        name='installment-condition-delete',
    ),
    url(r'^contracts/installments/$', views.AllInstallmentsView.as_view(), name='all-installments'),
    url(r'^contracts/', views.ContractsTableView.as_view(), name='contracts'),
    url(r'attachment/(?P<attachment_id>.+)/$', views.download_attachment, name='download_attachment'),
    url(r'^ajax/superset-query', views.presto_query, name='superset_query'),
    url(r'^', RedirectView.as_view(url='/contracts/'), name='redirect-url'),
]
