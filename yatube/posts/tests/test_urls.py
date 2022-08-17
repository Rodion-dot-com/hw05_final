from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PostsURLTests(TestCase):
    """Checking the correctness of the URLs in the app posts."""

    @classmethod
    def setUpClass(cls) -> None:
        """Creates the post in the database."""
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.author,
            group=cls.group,
        )

    def setUp(self) -> None:
        """Creates users for tests."""
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(PostsURLTests.author)

    def test_create_post_exists_at_desired_location_authorized(self) -> None:
        """The /create/ page is accessible to an authorized user."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_post_exists_at_desired_location_for_author(self) -> None:
        """The /posts/1/edit/ page is available to the author of the post."""
        response = self.authorized_client_author.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostsURLTests.post.id}
            )
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_post_redirect_authorized_on_post_page(self) -> None:
        """
        The /posts/1/edit/ page redirects the authorized user to the
        post's page.
        """
        response = self.authorized_client.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostsURLTests.post.id}
            ),
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostsURLTests.post.id}
            )
        )

    def test_publicly_available_url_exists_at_desired_location(self) -> None:
        """
        Checks if there are exists at desired location of pages accessible
        to unauthorized users.
        """
        urls = (
            reverse('posts:index'),
            reverse(
                'posts:group_list',
                kwargs={'slug': PostsURLTests.group.slug}
            ),
            reverse(
                'posts:profile',
                kwargs={'username': PostsURLTests.author.username}
            ),
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostsURLTests.post.id}
            ),
        )
        for address in urls:
            with self.subTest(adress=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_for_authorized_redirect_anonymous(self) -> None:
        """Checks the correctness of redirecting unauthorized users."""
        redirect_address = reverse('users:login')
        urls = (
            reverse('posts:post_create'),
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostsURLTests.post.id}
            ),
        )
        for address in urls:
            with self.subTest(adress=address):
                response = self.guest_client.get(address, follow=True)
                self.assertRedirects(response, f'{redirect_address}'
                                               f'?next={address}')

    def test_unexisting_page(self) -> None:
        """
        Checks that a request to an unexisting page will return a 404 error.
        """
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')

    def test_is_correct_template_for_url_unauthorized(self) -> None:
        """
        Checks that the correct templates are used for unauthorized users.
        """
        urls_templates = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': PostsURLTests.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': PostsURLTests.author.username}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostsURLTests.post.id}
            ): 'posts/post_detail.html',
        }
        for address, template in urls_templates.items():
            with self.subTest(adress=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_is_correct_template_for_url_authorized(self) -> None:
        """
        Checks if the correct templates are being used for authorized users.
        """
        urls_templates = {
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for address, template in urls_templates.items():
            with self.subTest(adress=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_is_correct_template_for_post_edit(self) -> None:
        """
        Checks if the correct template is used for /posts/1/edit/
        for the author of the post.
        """
        response = self.authorized_client_author.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostsURLTests.post.id}
            )
        )
        self.assertTemplateUsed(response, 'posts/create_post.html')
