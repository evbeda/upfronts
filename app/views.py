import csv
import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.forms import DateInput
from django.http import (
    HttpResponse,
    JsonResponse,
)
from django.shortcuts import redirect
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
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

from app import (
    BASIC_CONDITIONS,
    SUPERSET_DEFAULT_CURRENCY,
    LINK_TO_RECOUPS,
    LINK_TO_REPORT_EVENTS,
    LINK_TO_SEARCH_EVENT_OR_USER,
    STATUS,
    SUPERSET_QUERY_DATE_FORMAT,
)
from app.models import (
    Contract,
    Installment,
    InstallmentCondition,
)
from app.tables import (
    ContractsTable,
    FetchSalesForceCasesTable,
    InstallmentsTable,
)
from app.utils import (
    fetch_cases,
    fetch_cases_by_date,
    generate_presto_query,
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['info_event_url'] = LINK_TO_SEARCH_EVENT_OR_USER.format(
            email_organizer=context['object'].organizer_email)
        return context


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
        context['link_to_recoup'] = LINK_TO_RECOUPS
        context['link_to_event'] = LINK_TO_REPORT_EVENTS.format(contract.event_id)
        context['form'].fields['maximum_payment_date'].widget = DateInput(
            attrs={
                'id': 'datepicker_maximum_payment_date',
                'type': 'text',
            },
        )
        context['form'].fields['payment_date'].widget = DateInput(
            attrs={
                'id': 'datepicker_payment_date',
                'type': 'text',
            },
        )
        return context

    def get_success_url(self):
        return reverse_lazy('installments-create', kwargs=self.kwargs)

    def form_valid(self, form, **kwargs):
        form.instance.contract_id = self.kwargs['contract_id']
        self.object = form.save()
        for condition in BASIC_CONDITIONS:
            InstallmentCondition.objects.create(
                installment=self.object,
                condition_name=condition,
            )
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
            installment.contract.organizer_email,
            installment.contract.signed_date,
            installment.upfront_projection,
            installment.recoup_amount,
            installment.balance,
            installment.maximum_payment_date,
            installment.payment_date,
            installment.gts,
            installment.gtf,
        ])
    return response


class ContractAdd(TemplateView):

    template_name = "app/add_contracts.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        case_numbers = self.request.GET.get('case_numbers') or self.kwargs.get('case_numbers')
        date_from = self.request.GET.get('case_date_from')
        date_to = self.request.GET.get('case_date_to')
        contract_data = []
        if date_from or date_to:
            try:
                date_from_formated = '{2}-{0}-{1}T00:00:00.000+0000'.format(*date_from.split('/'))
                date_to_formated = '{2}-{0}-{1}T23:59:59.000+0000'.format(*date_to.split('/'))
                contract_data = fetch_cases_by_date(date_from_formated, date_to_formated)
                for elem in contract_data:
                    elem['save'] = elem['case_id']
                    context["table"] = FetchSalesForceCasesTable(contract_data)
            except Exception:
                context["message"] = "Please enter both dates"
        if case_numbers:
            try:
                contract_data = fetch_cases(case_numbers)
                for elem in contract_data:
                    elem['save'] = elem['case_id']
                context['table'] = FetchSalesForceCasesTable(contract_data)
            except Exception:
                context["message"] = "This case number: '{}' doesn't exist".format(case_numbers)
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
            link_to_salesforce_case=case_data['Case_URL__c'],
        )
        return redirect('installments-create', contract.id)


class ConditionView(LoginRequiredMixin, CreateView):
    template_name = "app/create_condition.html"
    model = InstallmentCondition
    fields = [
        'id',
        'condition_name',
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        installment = Installment.objects.filter(id=self.kwargs['installment_id']).get()

        context['installment'] = installment
        context['object_list'] = InstallmentCondition.objects.filter(installment_id=self.kwargs['installment_id']).all()
        context['SUPERSET_DEFAULT_CURRENCY'] = SUPERSET_DEFAULT_CURRENCY

        return context

    def get_success_url(self):
        return reverse_lazy('conditions', kwargs=self.kwargs)

    def form_valid(self, form, **kwargs):
        form.instance.installment_id = self.kwargs['installment_id']
        self.object = form.save()
        return super(ConditionView, self).form_valid(form)


class ToggleConditionView(View):
    def post(self, request, *args, **kwargs):
        contract_id = self.kwargs.get('contract_id')
        installment_id = self.kwargs.get('installment_id')

        condition_id = self.kwargs.get('condition_id')
        condition = InstallmentCondition.objects.get(pk=condition_id)
        condition.toggle_done()
        return redirect('conditions', contract_id, installment_id)


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
                    installment.contract.organizer_email,
                    installment.contract.signed_date,
                    installment.upfront_projection,
                    installment.recoup_amount,
                    installment.maximum_payment_date,
                    installment.payment_date,
                    installment.gts,
                    installment.gtf,
                ])
            return response
        return filtered_response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url'] = self.request.get_full_path()
        return context


def presto_query(request):
    query_params = request.GET

    event_id = query_params.get('event-id')
    from_date = datetime.datetime.strptime(
        query_params.get('from-date'),
        SUPERSET_QUERY_DATE_FORMAT,
    ) if query_params.get('from-date') else None

    to_date = datetime.datetime.strptime(
        query_params.get('to-date'),
        SUPERSET_QUERY_DATE_FORMAT,
    ) if query_params.get('to-date') else None
    currency = query_params.get('currency')

    query = generate_presto_query(event_id, from_date, to_date, currency)
    return JsonResponse({'query': query})


class InstallmentUpdate(UpdateView):
    model = Installment
    fields = (
        'is_recoup',
        'status',
        'upfront_projection',
        'maximum_payment_date',
        'payment_date',
        'recoup_amount',
        'gtf',
        'gts',
    )
    template_name = "app/update_installment.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'].fields['maximum_payment_date'].widget = DateInput(
            attrs={
                'id': 'datepicker_maximum_payment_date',
                'type': 'text',
            },
        )
        context['form'].fields['payment_date'].widget = DateInput(
            attrs={
                'id': 'datepicker_payment_date',
                'type': 'text',
            },
        )
        return context

    def get_success_url(self):
        return reverse_lazy('installments-create', kwargs={'contract_id': self.kwargs['contract_id']})


class InstallmentDelete(DeleteView):
    model = Installment
    template_name = "app/delete_installment.html"

    def post(self, request, *args, **kwargs):
        contract_id = kwargs['contract_id']
        self.get_queryset().filter(id=kwargs['pk']).delete()
        return redirect("installments-create", contract_id)
