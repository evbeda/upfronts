from django.utils.html import format_html
from django.urls import reverse
import django_tables2 as tables

from .models import Installment


class InstallmentsTable(tables.Table):
    edit = tables.Column()

    class Meta:
        model = Installment
        template_name = "django_tables2/bootstrap.html"
        exclude = ('id', 'gtf', 'gts')
        fields = (
            'is_recoup',
            'status',
            'contract.event_id',
            'contract.user_id',
            'contract.organizer_account_name',
            'contract.organizer_email',
            'upfront_projection',
            'maximum_payment_date',
            'payment_date',
            'recoup_amount',
        )

    def render_installment_projection(self, value):
        return '${:0.2f}'.format(value)

    def render_edit(self, value):
        # / installments / update / {} /
        return format_html(
            '<a href="{}"> Edit</a>'.format(reverse('installments-update', args=(value.id,)))
        )

    def render_recoup_amount(self, value):
        return '${:0.2f}'.format(value)
