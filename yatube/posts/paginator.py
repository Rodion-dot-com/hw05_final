from django.core.paginator import Page, Paginator
from django.db.models import QuerySet
from django.http import HttpRequest


def split_into_pages(request: HttpRequest, posts: QuerySet,
                     max_sample_size: int) -> Page:
    """
    Splits the list of posts into pages and returns the desired page.

    Args:
        request (HttpRequest): A basic HTTP request.
        posts (QuerySet): List of posts to be paginated.
        max_sample_size (int): Maximum number of posts per page.
    """
    paginator = Paginator(posts, max_sample_size)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
