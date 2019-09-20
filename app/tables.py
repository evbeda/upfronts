import django_tables2 as tables
from .models import Upfront


class UpfrontTable(tables.Table):

    class Meta:
        model = Upfront
        template_name = "django_tables2/bootstrap.html"
        exclude = ('id', 'gtf', 'gts')
        # fields = ('is_recoup', 'status','organizer', )

    def render_upfront_projection(self, value):
        return '${:0.2f}'.format(value)

    def render_recoup_amount(self, value):
        return '${:0.2f}'.format(value)

    def render_gtf(self, value):
        return '${:0.2f}'.format(value)

    def render_gts(self, value):
        return '${:0.2f}'.format(value)
