import json

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http.request import HttpRequest

from {{ app.app_name }} import manager


log = manager.get_logger_for_pyfile(__file__)


class ConfigView(LoginRequiredMixin, TemplateView):
    """Included as example."""

    template_name = f'main/config.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        config_as_indented_text = json.dumps(
            manager.config.as_dict(), indent=4)
        context['config'] = f'\n{config_as_indented_text}'
        return context
