import csv
import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
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
from app.tables import InstallmentsTable


class InstallmentsFilter(FilterSet):

    organizer_search = CharFilter(label='Organizer', method='search_organizer')
    signed_date_search = DateFilter(label='Contract signed date', method='search_signed_date')

    def search_organizer(self, qs, name, value):
        return qs.filter(
            Q(contract__organizer_account_name__icontains=value) |
            Q(contract__organizer_email__icontains=value)
        )

    def search_signed_date(self, qs, name, value):
        return qs.filter(
            Q(contract__signed_date=value)
        )

    class Meta:
        model = Installment
        fields = ('organizer_search',)


class InstallmentsTableView(LoginRequiredMixin, SingleTableMixin, FilterView):
    queryset = Installment.objects.all()
    table_class = InstallmentsTable
    template_name = "app/installment_table.html"
    filterset_class = InstallmentsFilter


class InstallmentUpdate(UpdateView):
    template_name = "app/update_installment.html"
    model = Contract
    fields = ["organizer_account_name", "organizer_email", "signed_date", "event_id", "user_id"]

    def get_success_url(self):
        return reverse_lazy('installments')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pk'] = self.kwargs['pk']
        return context


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
