import shutil
import tempfile
from http import HTTPStatus

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpResponse
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post
from ..views import MAX_SAMPLE_SIZE

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    """Checking the correctness of the views in the app posts."""

    @classmethod
    def setUpClass(cls) -> None:
        """Creates the post in the database."""
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.image = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group,
            image=cls.image,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self) -> None:
        """Creates users for tests."""
        cache.clear()
        self.guest_client = Client()
        self.user = PostPagesTests.user
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(self.user)

    def context_contains_expected_post(self, response: HttpResponse) -> None:
        """Checks whether the page contains the expected post."""
        self.assertContains(response, PostPagesTests.post)
        for post in response.context['page_obj']:
            if post.id == PostPagesTests.post.id:
                self.assertEqual(post.author, PostPagesTests.post.author)
                self.assertEqual(post.group, PostPagesTests.post.group)
                self.assertEqual(post.text, PostPagesTests.post.text)
                self.assertEqual(post.image, PostPagesTests.post.image)

    def test_pages_uses_correct_template(self) -> None:
        """The URL uses the appropriate template."""
        pages_names_templates = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': PostPagesTests.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': PostPagesTests.user.username}
            ): 'posts/profile.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostPagesTests.post.id}
            ): 'posts/create_post.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostPagesTests.post.id}
            ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in pages_names_templates.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client_author.get(reverse_name)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_create_edit_page_show_correct_context(self) -> None:
        """The context in the create_post and edit_post pages is correct."""
        reverse_name_context = {
            reverse('posts:post_create'): {'is_edit': False},
            reverse(
                'posts:post_edit', kwargs={'post_id': PostPagesTests.post.id}
            ): {'is_edit': True},
        }
        for reverse_name, context in reverse_name_context.items():
            with self.subTest(reverse_name=reverse_name):
                form_fields = {
                    'text': forms.fields.CharField,
                    'group': forms.fields.ChoiceField,
                    'image': forms.fields.ImageField,
                }
                response = self.authorized_client_author.get(reverse_name)
                self.assertEqual(
                    len(form_fields),
                    len(response.context.get('form').fields)
                )

                for form_field, expected in form_fields.items():
                    with self.subTest(form_field=form_field):
                        form_field = response.context.get('form').fields.get(
                            form_field)
                        self.assertIsInstance(form_field, expected)

                self.assertEqual(
                    response.context.get('is_edit'),
                    context['is_edit']
                )

    def test_index_page_show_correct_context(self) -> None:
        """The context in the index page is correct."""
        response = self.authorized_client_author.get(reverse('posts:index'))

        expected_title = 'Это главная страница проекта Yatube'
        self.assertEqual(expected_title, response.context.get('title'))

        self.context_contains_expected_post(response)

    def test_post_detail_page_show_correct_context(self) -> None:
        """The context in the post_detail page is correct."""
        response = self.authorized_client_author.get(reverse(
            'posts:post_detail', kwargs={'post_id': 1}))

        expected_post = PostPagesTests.post
        expected_text_in_title = expected_post.__str__()
        expected_posts_count_by_author = 1
        expected_is_author = True

        expected_context = {
            'post': expected_post,
            'text_in_title': expected_text_in_title,
            'count': expected_posts_count_by_author,
            'is_author': expected_is_author,
        }

        for value, expected in expected_context.items():
            with self.subTest(value=value):
                self.assertEqual(response.context.get(value), expected)

        self.assertEqual(response.context.get('post').image,
                         expected_post.image)

    def test_group_posts_page_show_correct_context(self) -> None:
        """The context in the group_posts page is correct."""
        response = self.authorized_client_author.get(reverse(
            'posts:group_list', kwargs={'slug': 'test-slug'}))

        expected_group = PostPagesTests.group
        self.assertEqual(expected_group, response.context.get('group'))

        self.context_contains_expected_post(response)

    def test_profile_page_show_correct_context(self) -> None:
        """The context in the profile page is correct."""
        response = self.authorized_client_author.get(reverse(
            'posts:profile', kwargs={'username': 'auth'}))

        expected_author = PostPagesTests.user
        self.assertEqual(expected_author, response.context.get('author'))

        expected_posts_count_by_author = 1
        self.assertEqual(response.context.get('count'),
                         expected_posts_count_by_author)

        self.context_contains_expected_post(response)


class PostPaginatorTests(TestCase):
    """Checking the correctness of the paginator in the app posts."""

    @classmethod
    def setUpClass(cls):
        """Creates the posts in the database."""
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.posts_count = 15
        cls.posts = Post.objects.bulk_create([
            Post(
                text=f'Текстовый пост №{i}',
                author=cls.user,
                group=cls.group,
            ) for i in range(cls.posts_count)
        ])
        cls.reverse_names_of_views_for_testing = (
            reverse('posts:index'),
            reverse(
                'posts:group_list',
                kwargs={'slug': PostPaginatorTests.group.slug}
            ),
            reverse(
                'posts:profile',
                kwargs={'username': PostPaginatorTests.user.username}
            ),
        )

    def setUp(self) -> None:
        """Creates user for tests."""
        cache.clear()
        self.guest_client = Client()

    def test_pages_contain_expected_number_records(self) -> None:
        """The number of posts on the pages is displayed correctly."""
        page_number_posts_count = {
            1: MAX_SAMPLE_SIZE,
            2: PostPaginatorTests.posts_count % MAX_SAMPLE_SIZE,
        }
        for page_number, posts_count in page_number_posts_count.items():
            for reverse_name in (
                    PostPaginatorTests.reverse_names_of_views_for_testing):
                with self.subTest(reverse_name=reverse_name):
                    response = self.guest_client.get(
                        reverse_name,
                        {'page': page_number}
                    )
                    self.assertEqual(
                        len(response.context['page_obj']),
                        posts_count
                    )


class ViewAfterNewPostTests(TestCase):
    """Additional view check when creating a post."""

    @classmethod
    def setUpClass(cls) -> None:
        """Creates users, groups, and a post in the database."""
        super().setUpClass()
        cls.user1 = User.objects.create_user(username='auth')
        cls.user2 = User.objects.create_user(username='HasNoName')
        cls.group1 = Group.objects.create(
            title='Первая тестовая группа',
            slug='test-slug1',
            description='Тестовое описание',
        )
        cls.group2 = Group.objects.create(
            title='Вторая тестовая группа',
            slug='test-slug2',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Текстовый пост 11',
            author=cls.user1,
            group=cls.group1,
        )

    def setUp(self) -> None:
        """Creates user for tests."""
        cache.clear()
        self.guest_client = Client()

    def test_post_not_displayed_on_non_intended_pages(self) -> None:
        """The post did not get to the pages for which it was not intended."""
        reverse_names = (
            reverse(
                'posts:group_list',
                kwargs={'slug': ViewAfterNewPostTests.group2.slug}
            ),
            reverse(
                'posts:profile',
                kwargs={'username': ViewAfterNewPostTests.user2.username}
            ),
        )

        for reverse_name in reverse_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertNotContains(response, ViewAfterNewPostTests.post)


class PostCommentsTests(TestCase):
    """Checking whether comments are displayed correctly."""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.author
        )
        cls.comment = Comment.objects.create(
            text='Тестовый комментарий',
            author=cls.author,
            post=cls.post
        )

    def setUp(self) -> None:
        """Creates user for tests."""
        cache.clear()
        self.guest_client = Client()

    def test_post_detail_displays_comment(self) -> None:
        """The created comment is displayed on the post_detail page."""
        response = self.guest_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': PostCommentsTests.post.id})
        )
        self.assertContains(response, PostCommentsTests.comment)


class CachePagesTests(TestCase):
    """Checking the correctness of the cache."""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.guest_client = Client()
        cls.author = User.objects.create_user(username='auth')

    def setUp(self) -> None:
        cache.clear()

    def test_index_new_post_not_in_cache(self) -> None:
        """
        When creating a post after a request to the index page, the post is
        not displayed on the index page.
        """
        CachePagesTests.guest_client.get(reverse('posts:index'))

        new_post = Post.objects.create(
            text='Новый пост',
            author=CachePagesTests.author
        )
        new_response = CachePagesTests.guest_client.get(
            reverse('posts:index')
        )
        self.assertNotContains(new_response, new_post)

        cache.clear()
        response_with_new_cache = CachePagesTests.guest_client.get(
            reverse('posts:index')
        )
        self.assertContains(response_with_new_cache, new_post)


class FollowPagesTests(TestCase):
    """Follow pages work correctly."""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.author
        )

    def setUp(self) -> None:
        self.user = User.objects.create_user(username='name')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_follow_index_not_contain_post(self) -> None:
        """
        If the user is not subscribed to the author, follow_index will not
        contain posts by this author.
        """
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertNotContains(response, FollowPagesTests.post)

    def test_profile_follow(self) -> None:
        """
        After subscribing to the author, the post is displayed in
        follow_index.
        """
        self.authorized_client.post(
            reverse('posts:profile_follow',
                    kwargs={'username': FollowPagesTests.author.username})
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertContains(response, FollowPagesTests.post)

    def test_profile_unfollow(self) -> None:
        """
        After unsubscribing to the author, the post is not displayed in
        follow_index.
        """
        self.authorized_client.post(
            reverse('posts:profile_follow',
                    kwargs={'username': FollowPagesTests.author.username})
        )
        self.authorized_client.post(
            reverse('posts:profile_unfollow',
                    kwargs={'username': FollowPagesTests.author.username})
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertNotContains(response, FollowPagesTests.post)
