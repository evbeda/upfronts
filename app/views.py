# from django.contrib.auth.mixins import LoginRequiredMixin
# from django.db.models import Q
# from django_filters import FilterSet, CharFilter, DateFilter
# from django_filters.views import FilterView
# from django_tables2.views import SingleTableMixin
#
# from app.models import Upfront
# from .tables import UpfrontTable
#
#
# class UpfrontFilter(FilterSet):
#
#     organizer_search = CharFilter(label='Organizer', method='search_organizer')
#     signed_date_search = DateFilter(label='Contract signed date', method='search_signed_date')
#
#     def search_organizer(self, qs, name, value):
#         return qs.filter(
#             Q(organizer__icontains=value) |
#             Q(account_name__icontains=value) |
#             Q(email_organizer__icontains=value)
#         )
#
#     def search_signed_date(self, qs, name, value):
#         return qs.filter(
#             Q(contract_signed_date=value)
#         )
#
#     class Meta:
#         model = Upfront
#         fields = ('organizer_search',)
#
#
# class UpfrontsTableView(LoginRequiredMixin, SingleTableMixin, FilterView):
#     queryset = Upfront.objects.all()
#     table_class = UpfrontTable
#     template_name = "app/uf_table.html"
#     filterset_class = UpfrontFilter
