from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from . import forms
from .models import (MAX_NUMBER_CHARS_IN_POST_PRESENTATION, Follow, Group,
                     Post, User)
from .paginator import split_into_pages

MAX_SAMPLE_SIZE = 10


def index(request: HttpRequest) -> HttpResponse:
    """Renders the main page of the site."""
    template = 'posts/index.html'

    post_list = Post.objects.select_related('author', 'group')
    page_obj = split_into_pages(request, post_list, MAX_SAMPLE_SIZE)

    title = 'Это главная страница проекта Yatube'
    context = {
        'title': title,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request: HttpRequest, slug: str) -> HttpResponse:
    """
    Renders posts from a specific community, if there is no group with
    the specified slug throws Http404.

    Args:
        request (HttpRequest): A basic HTTP request.
        slug (str): Name to search in the group table.
    """
    template = 'posts/group_list.html'

    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related('author', 'group')
    page_obj = split_into_pages(request, post_list, MAX_SAMPLE_SIZE)

    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request: HttpRequest, username: str) -> HttpResponse:
    """
    Renders the user's posts by the specified name, if there is no user with
    the specified username throws Http404.

    Args:
        request (HttpRequest): A basic HTTP request.
        username (str): Name to search in the user table.
    """
    template = 'posts/profile.html'

    author = get_object_or_404(User, username=username)
    post_list = author.posts.select_related('author', 'group')
    page_obj = split_into_pages(request, post_list, MAX_SAMPLE_SIZE)

    following = (
        request.user.is_authenticated
        and Follow.objects.filter(user=request.user, author=author).exists()
    )

    is_author = (
        request.user.is_authenticated
        and request.user.username == username
    )

    context = {
        'author': author,
        'count': post_list.count(),
        'following': following,
        'is_author': is_author,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def post_detail(request: HttpRequest, post_id: int) -> HttpResponse:
    """
    Renders detailed information about the specified post, if there is no
    post with the desired id throws Http404.

    Args:
        request (HttpRequest): A basic HTTP request.
        post_id (int): Pk to search in the post table.
    """
    template = 'posts/post_detail.html'

    post = get_object_or_404(Post, id=post_id)
    text_in_title = post.text[:MAX_NUMBER_CHARS_IN_POST_PRESENTATION]
    count = post.author.posts.count()

    is_author = (request.user.id == post.author.id)

    comment_form = forms.CommentForm()
    comments = post.comments.select_related('author')

    context = {
        'post': post,
        'text_in_title': text_in_title,
        'count': count,
        'is_author': is_author,
        'form': comment_form,
        'comments': comments,
    }
    return render(request, template, context)


@login_required
def post_create(request: HttpRequest) -> HttpResponse:
    """
    Renders the form for creating a post and adds a new post to the database
    if the form is valid.
    """
    template = 'posts/create_post.html'
    form = forms.PostForm(request.POST or None, files=request.FILES or None)

    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=request.user.username)

    context = {
        'form': form,
        'is_edit': False,
    }
    return render(request, template, context)


@login_required
def post_edit(request: HttpRequest, post_id: int) -> HttpResponse:
    """
    Renders a form for editing a post and updates a post in the database if
    the user is the author of the post and the form is valid.

    Args:
        request (HttpRequest): A basic HTTP request.
        post_id (int): Pk to search in the post table.
    """
    template = 'posts/create_post.html'

    post = get_object_or_404(Post, id=post_id)

    if request.user.id != post.author.id:
        return redirect('posts:post_detail', post_id=post_id)

    form = forms.PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )

    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)

    context = {
        'post': post,
        'form': form,
        'is_edit': True,
    }
    return render(request, template, context)


@login_required
def add_comment(request: HttpRequest, post_id: int) -> HttpResponse:
    """
    Accepts comments to the specified post.

    Args:
        request (HttpRequest): A basic HTTP request.
        post_id (int): Pk to search in the post table.
    """
    form = forms.CommentForm(request.POST or None)
    post = get_object_or_404(Post, id=post_id)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request: HttpRequest) -> HttpResponse:
    """
    Renders a page with the posts of the authors to which the user is
    subscribed.
    """
    template = 'posts/follow.html'

    subscriptions = [follow.author for follow in request.user.follower.all()]
    posts = Post.objects.filter(author__in=subscriptions)

    page_obj = split_into_pages(request, posts, MAX_SAMPLE_SIZE)

    context = {
        'title': 'Избранные авторы',
        'page_obj': page_obj,
    }
    return render(request, template, context)


@login_required
def profile_follow(request: HttpRequest, username: str) -> HttpResponse:
    """Subscribes the user to the author by the specified username."""
    author = get_object_or_404(User, username=username)

    if request.user.username != author.username:
        Follow.objects.get_or_create(
            user=request.user,
            author=author
        )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request: HttpRequest, username: str) -> HttpResponse:
    """Unsubscribes the user from the author by the specified username."""
    author = get_object_or_404(User, username=username)

    subscriptions = Follow.objects.filter(user=request.user, author=author)
    if subscriptions.exists():
        subscriptions.delete()
    return redirect('posts:profile', username=username)
