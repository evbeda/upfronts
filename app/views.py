from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django_filters import FilterSet, CharFilter, DateFilter
from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin

from app.models import Installment
from .tables import InstallmentsTable


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
