from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class UpfrontsTableView(LoginRequiredMixin, TemplateView):
    template_name = "uf_table.html"
