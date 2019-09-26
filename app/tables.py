from django.urls import reverse
import django_tables2 as tables

from .models import Installment

class InstallmentsTable(tables.Table):
    actions = tables.Column(
        verbose_name=('Actions'),
        orderable=False,
        empty_values=(),
    )
    def render_actions(self, value, record):
        import ipdb;
        ipdb.set_trace()
        installment_url = reverse(
            'installments-update',
            kwargs={
                'event_id': record.event.id,
            },
        )

    class Meta:
        model = Installment
        template_name = "django_tables2/bootstrap.html"
        exclude = ('id', 'gtf', 'gts')
        fields = (
            'is_recoup',
            'status',
            'contract.organizer_account_name',
            'contract.organizer_email',
            'contract.event_id',
            'upfront_projection',
            'maximum_payment_date',
            'payment_date',
            'recoup_amount',
            'edit',
        )


    def render_installment_projection(self, value):
        return '${:0.2f}'.format(value)

    def render_recoup_amount(self, value):
        return '${:0.2f}'.format(value)
