import csv
import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.forms import DateInput
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import UpdateView
from django_filters import (
    CharFilter,
    DateFilter,
    FilterSet,
)
from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin

from app.models import Contract, Installment
from app.tables import (
    ContractsTable,
)


class ContractsFilter(FilterSet):

    organizer_search = CharFilter(label='Organizer', method='search_organizer')
    djfdate_time = DateFilter(
        label='Contract signed date',
        method='search_signed_date',
        lookup_expr='icontains',
        widget=DateInput(
            attrs={
                'id': 'datepicker',
                'type': 'text',
            },
        ),
    )

    def search_organizer(self, qs, name, value):
        return qs.filter(
            Q(organizer_account_name__icontains=value) |
            Q(organizer_email__icontains=value)
        )

    def search_signed_date(self, qs, name, value):
        return qs.filter(
            Q(signed_date=value)
        )

    class Meta:
        model = Contract
        fields = ('organizer_search',)


class ContractUpdate(UpdateView):
    template_name = "app/update_contract.html"
    model = Contract
    fields = ["organizer_account_name", "organizer_email", "signed_date", "event_id", "user_id"]
    success_url = reverse_lazy('contracts')


class ContractsTableView(LoginRequiredMixin, SingleTableMixin, FilterView):
    queryset = Contract.objects.all()
    table_class = ContractsTable
    template_name = "app/contracts_table.html"
    filterset_class = ContractsFilter


def download_csv(request):
    response = HttpResponse(content_type='text/csv')
    filename = "{}-upfronts.csv".format(datetime.datetime.now().replace(microsecond=0).isoformat())
    response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
    installments = Installment.objects.all()
    writer = csv.writer(response)
    for installment in installments:
        writer.writerow([
            installment.is_recoup,
            installment.status,
            installment.contract.organizer_account_name,
            installment.upfront_projection,
            installment.contract.organizer_email,
            installment.contract.signed_date,
            installment.contract.signed_date,
            installment.upfront_projection,
            installment.maximum_payment_date,
            installment.payment_date,
            installment.recoup_amount,
            installment.gts,
            installment.gtf,
        ])
    return response
