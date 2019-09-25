import django_tables2 as tables

from app.models import Installment


class InstallmentsTable(tables.Table):

    class Meta:
        model = Installment
        template_name = "django_tables2/bootstrap.html"
        exclude = ('id', 'gtf', 'gts')
        fields = (
            'is_recoup',
            'status',
            'contract.organizer_account_name',
            'contract.organizer_email',
            'upfront_projection',
            'maximum_payment_date',
            'payment_date',
            'recoup_amount',
        )

    def render_installment_projection(self, value):
        return '${:0.2f}'.format(value)

    def render_recoup_amount(self, value):
        return '${:0.2f}'.format(value)
