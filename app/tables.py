import datetime

from django.urls import reverse
from django.utils.html import format_html
import django_tables2 as tables

from app import (
    LINK_TO_REPORT_EVENTS,
    LINK_TO_RECOUPS,
)
from .models import (
    Contract,
    Installment,
)


class InstallmentsTable(tables.Table):
    edit = tables.Column()
    delete = tables.Column()
    conditions = tables.Column()

    class Meta:
        model = Installment
        template_name = "django_tables2/bootstrap.html"
        exclude = ('id', 'gtf', 'gts')
        fields = (
            'is_recoup',
            'status',
            'upfront_projection',
            'recoup_amount',
            'balance',
            'maximum_payment_date',
            'payment_date',
        )

    def render_upfront_projection(self, value):
        return '${:0.2f}'.format(value)

    def render_recoup_amount(self, value):
        return '${:0.2f}'.format(value)

    def render_balance(self, value):
        return '${:0.2f}'.format(value)

    def render_edit(self, value):
        return format_html(
            '<a href="{}"><i class="far fa-edit"></i></a>'.format(
                reverse('installments-update', args=[value.contract_id, value.id])
            )
        )

    def render_delete(self, value):
        return format_html(
            '<a href="{}"><i class="far fa-trash-alt"></i></a>'.format(
                reverse('installments-delete', args=[value.contract_id, value.id])
            )
        )

    def render_conditions(self, value):
        return format_html(
            '<a href="{}"><i class="fas fa-list"></i></a>'.format(reverse(
                'conditions', args=(value.contract_id, value.id))
            )
        )


class ContractsTable(tables.Table):
    installments = tables.Column(orderable=False)
    details = tables.Column(orderable=False)

    class Meta:
        model = Contract

        row_attrs = {
            "align": 'center'
        }
        template_name = "django_tables2/bootstrap.html"
        exclude = ('id',)
        fields = (
            'organizer_account_name',
            'organizer_email',
            'user_id',
            'signed_date',
        )

    def render_details(self, value):
        return format_html(
            '<a href="{}"><i class="fas fa-stream"></i></a>'.format(reverse(
                'contracts-detail', args=(value.id,))
            )
        )

    def render_installments(self, value):
        return format_html(
            '<a href="{}"><i class="fas fa-list"></i></a>'.format(reverse('installments-create', args=(value.id,))),
        )

    def render_event_id(self, value):
        link = LINK_TO_REPORT_EVENTS.format(value)
        return format_html(
            '<a href="{}">{}</a>'.format(link, value))

    def render_user_id(self, value):
        link = LINK_TO_RECOUPS
        return format_html(
            '<a href="{}">{}</a>'.format(link, value))


class FetchSalesForceCasesTable(tables.Table):
    case_number = tables.Column()
    case_id = tables.Column()
    organizer_name = tables.Column()
    organizer_email = tables.Column()
    signed_date = tables.Column()
    contract_id = tables.Column()
    save = tables.Column(orderable=False)

    class Meta:
        template_name = "django_tables2/bootstrap.html"

    def render_case_id(self, value):
        link_to_salesforce_case = self.data.data[0]['link_to_salesforce_case']
        return format_html(
            '''<a href="{}">{}</a>'''.format(link_to_salesforce_case, value)
        )

    def render_save(self, value):
        if Contract.objects.filter(salesforce_case_id=value).first():
            return format_html(
                '<p>This contract already exists.</p>'
            )
        return format_html(
            '''<form method="POST" action="{}">
                <button type="submit" class="btn btn-link"><i class="far fa-save fa-lg"></i></button>
            </form>'''.format(reverse('contracts-save', args=(value,)))
        )

    def render_signed_date(self, value):
        dt = datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f%z")
        return dt.strftime("%m/%d/%Y")
