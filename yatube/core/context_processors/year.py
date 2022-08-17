from datetime import date


def year(request):
    """Adds the year variable with the current year to the context."""
    return {
        'year': date.today().year
    }
