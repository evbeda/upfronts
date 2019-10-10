import datetime

from django.urls import reverse
from django.utils.html import format_html
import django_tables2 as tables

from .models import (
    Contract,
    Installment,
)


class InstallmentsTable(tables.Table):
    edit = tables.Column()
    conditions = tables.Column()

    class Meta:
        model = Installment
        template_name = "django_tables2/bootstrap.html"
        exclude = ('id', 'gtf', 'gts')
        fields = (
            'is_recoup',
            'status',
            'upfront_projection',
            'maximum_payment_date',
            'payment_date',
            'recoup_amount',
        )

    def render_installment_projection(self, value):
        return '${:0.2f}'.format(value)

    def render_edit(self, value):
        return format_html('<a href="#"><i class="far fa-edit"></i></a>')

    def render_recoup_amount(self, value):
        return '${:0.2f}'.format(value)

    def render_conditions(self, value):
        return format_html(
            '<a href="{}"><i class="fas fa-list"></i></a>'.format(reverse(
                'conditions', args=(value.contract_id, value.id))
            )
        )


class ContractsTable(tables.Table):
    installments = tables.Column(orderable=False)
    edit = tables.Column(orderable=False)

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
            'event_id',
            'signed_date',
        )

    def render_edit(self, value):
        return format_html(
            '<a href="{}"><i class="far fa-edit"></i></a>'.format(reverse(
                'contracts-update', args=(value.id,))
            )
        )

    def render_installments(self, value):
        return format_html(
            '<a href="{}"><i class="fas fa-list"></i></a>'.format(reverse('installments-create', args=(value.id,))),
        )


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

    def render_save(self, value):
        return format_html(
            '''<form method="POST" action="{}">
                <button type="submit" class="btn btn-link"><i class="far fa-save fa-lg"></i></button>
            </form>'''.format(reverse('contracts-save', args=(value,)))
        )

    def render_signed_date(self, value):
        dt = datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f%z")
        return dt.strftime("%m/%d/%Y")
