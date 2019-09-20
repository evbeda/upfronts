import csv
import datetime
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django_filters import FilterSet, CharFilter, DateFilter
from django_filters.views import FilterView
from django.http import HttpResponse
from django_tables2.views import SingleTableMixin

from app.models import Upfront
from .tables import UpfrontTable


class UpfrontFilter(FilterSet):

    organizer_search = CharFilter(label='Organizer', method='search_organizer')
    signed_date_search = DateFilter(label='Contract signed date', method='search_signed_date')

    def search_organizer(self, qs, name, value):
        return qs.filter(
            Q(organizer__icontains=value) |
            Q(account_name__icontains=value) |
            Q(email_organizer__icontains=value)
        )

    def search_signed_date(self, qs, name, value):
        return qs.filter(
            Q(contract_signed_date=value)
        )

    class Meta:
        model = Upfront
        fields = ('organizer_search',)


class UpfrontsTableView(LoginRequiredMixin, SingleTableMixin, FilterView):
    queryset = Upfront.objects.all()
    table_class = UpfrontTable
    template_name = "app/uf_table.html"
    filterset_class = UpfrontFilter


def download_csv(request):
    response = HttpResponse(content_type='text/csv')
    filename = "{}-upfronts.csv".format(datetime.datetime.now().replace(microsecond=0).isoformat())
    response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
    upfronts = Upfront.objects.all()
    writer = csv.writer(response)
    for upfront in upfronts:
        writer.writerow([
            upfront.is_recoup,
            upfront.status,
            upfront.organizer,
            upfront.account_name,
            upfront.email_organizer,
            upfront.upfront_projection,
            upfront.contract_signed_date,
            upfront.maximum_payment_date,
            upfront.payment_date,
            upfront.recoup_amount,
            upfront.gts,
            upfront.gtf
        ])
    return response
