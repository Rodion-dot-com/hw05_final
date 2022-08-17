from django.views.generic.base import TemplateView


class AboutAuthorView(TemplateView):
    """Renders information about the author."""
    template_name = 'about/author.html'


class AboutTechView(TemplateView):
    """Renders information about the technologies in the project."""
    template_name = 'about/tech.html'
