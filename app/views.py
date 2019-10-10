import csv
import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.forms import DateInput
from django.http import HttpResponse
from django.shortcuts import redirect
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    ListView,
    UpdateView,
    TemplateView,
)
from django_filters import (
    CharFilter,
    ChoiceFilter,
    DateFilter,
    FilterSet,
)
from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin
from django.utils.decorators import method_decorator

from app import STATUS
from app.models import (
    Contract,
    Installment
)
from app.tables import (
    ContractsTable,
    FetchSalesForceCasesTable,
    InstallmentsTable,
)
from app.utils import (
    fetch_cases,
    get_case_by_id,
    get_contract_by_id,
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


class InstallmentView(LoginRequiredMixin, SingleTableMixin, CreateView):
    table_class = InstallmentsTable
    template_name = "app/create_installment.html"
    model = Installment
    fields = [
        "is_recoup",
        "status",
        "upfront_projection",
        "maximum_payment_date",
        "payment_date",
        "recoup_amount",
        "gtf",
        "gts",
    ]

    def get_queryset(self):
        queryset = Installment.objects.filter(contract_id=self.kwargs['contract_id'])
        return queryset.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contract = Contract.objects.filter(id=self.kwargs['contract_id']).get()
        context['contract'] = contract
        return context

    def get_success_url(self):
        return reverse_lazy('installments-create', kwargs=self.kwargs)

    def form_valid(self, form, **kwargs):
        form.instance.contract_id = self.kwargs['contract_id']
        self.object = form.save()
        return super(InstallmentView, self).form_valid(form)


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


class ContractAdd(TemplateView):

    template_name = "app/add_contracts.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        case_numbers = self.request.GET.get('case_numbers') or self.kwargs.get('case_numbers')
        if case_numbers:
            contract_data = fetch_cases(case_numbers)
            for elem in contract_data:
                elem['save'] = elem['case_id']
            context["table"] = FetchSalesForceCasesTable(contract_data)
        return context


@method_decorator(csrf_exempt, name='dispatch')
class SaveCaseView(View):

    def post(self, request, *args, **kwargs):
        case_id = self.kwargs['contract_id']
        case_data = get_case_by_id(case_id)
        contract_id = case_data['Contract__c']
        contract_data = get_contract_by_id(contract_id)
        contract = Contract.objects.create(
            organizer_account_name=contract_data['Hoopla_Account_Name__c'],
            organizer_email=contract_data['Eventbrite_Username__c'],
            signed_date=datetime.datetime.strptime(contract_data['ActivatedDate'], "%Y-%m-%dT%H:%M:%S.%f%z"),
            description=case_data['Description'],
            case_number=case_data['CaseNumber'],
            salesforce_id=contract_id,
            salesforce_case_id=case_id,
        )
        return redirect('installments-create', contract.id)


class InstallmentsFilter(FilterSet):
    search_organizer = CharFilter(
        label='Search organizer',
        method='search_contract_organizer',
        lookup_expr='icontains',
    )
    djfdate_time_signed_date = DateFilter(
        label='Signed date',
        method='search_contract_signed_date',
        lookup_expr='icontains',
        widget=DateInput(
            attrs={
                'id': 'datepicker_signed_date',
                'type': 'text',
            },
        ),
    )
    djfdate_time_max_payment_date = DateFilter(
        label='Max payment date',
        method='search_maximum_payment_date',
        lookup_expr='icontains',
        widget=DateInput(
            attrs={
                'id': 'datepicker_max_payment_date',
                'type': 'text',
            },
        ),
    )
    djfdate_ttime_payment_date = DateFilter(
        label='Payment date',
        method='search_payment_date',
        lookup_expr='icontains',
        widget=DateInput(
            attrs={
                'id': 'datepicker_payment_date',
                'type': 'text',
            },
        ),
    )
    status = ChoiceFilter(
        choices=STATUS,
        # initial='COMMITED/APPROVED',
        # label='Status',
        empty_label='Status options',
        method='search_status',
        lookup_expr='icontains',
    )

    def search_payment_date(self, qs, name, value):
        return qs.filter(
            Q(payment_date=value)
        )

    def search_maximum_payment_date(self, qs, name, value):
        return qs.filter(
            Q(maximum_payment_date=value)
        )

    def search_status(self, qs, name, value):
        return qs.filter(
            Q(status__icontains=value)
        )

    def search_contract_signed_date(self, qs, name, value):
        return qs.filter(
            Q(contract__signed_date__icontains=value)
        )

    def search_contract_organizer(self, qs, name, value):
        return qs.filter(
            Q(contract__organizer_account_name__icontains=value) |
            Q(contract__organizer_email__icontains=value)
        )

    class Meta:
        model = Installment
        fields = ('search_organizer',)


class AllInstallmentsView(LoginRequiredMixin, FilterView, ListView):
    model = Installment
    template_name = "app/all-installments.html"
    filterset_class = InstallmentsFilter

    def get(self, request, *args, **kwargs):
        filtered_response = super().get(request, *args, **kwargs)
        if 'download' in filtered_response.context_data['url']:
            response = HttpResponse(content_type='text/csv')
            filename = "{}-upfronts.csv".format(datetime.datetime.now().replace(microsecond=0).isoformat())
            response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
            installments = filtered_response.context_data['installment_list']
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
        return filtered_response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url'] = self.request.get_full_path()
        return context
