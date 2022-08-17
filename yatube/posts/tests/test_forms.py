import shutil
import tempfile
from typing import List

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormsTests(TestCase):
    """Verifying the correctness of forms associated with the post model."""

    @classmethod
    def setUpClass(cls) -> None:
        """Creates an authorized user."""
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='auth')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self) -> None:
        """Creates a group and posts for tests."""
        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        posts_count = 15
        self.posts = Post.objects.bulk_create([
            Post(
                text=f'Текстовый пост №{i}',
                author=PostFormsTests.user,
                group=self.group,
            ) for i in range(posts_count)
        ])

    def unexpected_posts_not_changed(self, posts_before: List[Post]) -> None:
        """
        Checks that unexpected records in the database have not been changed.
        """
        posts_after = Post.objects.all()
        for post_before, post_after in zip(posts_before, posts_after):
            with self.subTest(post_before=post_before):
                self.assertEqual(post_before.id, post_after.id)
                self.assertEqual(post_before.text, post_after.text)
                self.assertEqual(post_before.pub_date, post_after.pub_date)
                self.assertEqual(post_before.author, post_after.author)
                self.assertEqual(post_before.group, post_after.group)
                self.assertEqual(post_before.image, post_after.image)

    def test_adding_post_to_db(self) -> None:
        """
        When submitting a valid form, post_create creates a new post in the
        database and does not change the rest.
        """
        posts_count_before = Post.objects.count()
        posts_before = Post.objects.all()
        form_data = {
            'text': 'Тестовый пост',
        }
        PostFormsTests.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
        )
        self.assertEqual(Post.objects.count(), posts_count_before + 1)

        latest_post = Post.objects.latest('id')
        self.assertEqual(latest_post.text, form_data['text'])
        self.assertEqual(latest_post.author, PostFormsTests.user)
        self.assertIsNone(latest_post.group)

        self.unexpected_posts_not_changed(posts_before)

    def test_editing_post_in_db(self) -> None:
        """
        When submitting a valid form, edit_post changes the expected post in
        the database and does not change the rest.
        """
        posts_before = Post.objects.all()
        old_group = self.group
        post = Post.objects.create(
            text='Тестовый пост',
            author=PostFormsTests.user,
            group=old_group
        )
        post_id = post.id
        new_group = Group.objects.create(
            title='Новая тестовая группа',
            slug='test-slug-new',
            description='Тестовое описание новой группы',
        )
        pub_date_before = post.pub_date
        author_before = post.author

        posts_count = Post.objects.count()

        form_data = {
            'text': 'Тестовый пост, обновленный!',
            'group': new_group.id,
        }
        PostFormsTests.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post_id}),
            data=form_data,
            folow=True,
        )
        self.assertEqual(Post.objects.count(), posts_count)

        edited_post = Post.objects.get(id=post_id)

        self.assertEqual(edited_post.text, form_data['text'])
        self.assertEqual(edited_post.group.id, form_data['group'])

        self.assertEqual(edited_post.pub_date, pub_date_before)
        self.assertEqual(edited_post.author, author_before)

        with self.assertRaises(ObjectDoesNotExist):
            old_group.posts.get(id=post_id)

        self.unexpected_posts_not_changed(posts_before)

    def test_anonymous_editing_post_in_db(self) -> None:
        """
        When submitting a valid form by an anonymous user, edit_post does not
        change the posts in the database.
        """
        posts_count_before = Post.objects.count()
        posts_before = Post.objects.all()
        form_data = {
            'text': 'Тестовый пост от guest_client',
        }
        PostFormsTests.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
        )
        self.assertEqual(Post.objects.count(), posts_count_before)

        self.unexpected_posts_not_changed(posts_before)

    def test_adding_post_with_img_to_db(self) -> None:
        """
        When submitting a post with a picture through the PostForm form, a
        record is created in the database.
        """
        posts_count_before = Post.objects.count()
        posts_before = Post.objects.all()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый текст',
            'image': uploaded,
        }
        PostFormsTests.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
        )
        self.assertEqual(Post.objects.count(), posts_count_before + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст',
                image='posts/small.gif',
            ).exists()
        )
        self.unexpected_posts_not_changed(posts_before)


class CommentFormsTests(TestCase):
    """Verifying the correctness of forms associated with the comment model"""

    def setUp(self) -> None:
        self.guest_client = Client()
        self.author = User.objects.create_user(username='Author')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        self.post = Post.objects.create(
            text='Тестовый пост',
            author=self.author
        )

    def test_anonymous_adding_comment_in_db(self) -> None:
        """
        When submitting a valid form by an anonymous user, add_comment does
        not change the comments in the database.
        """
        comments_count_before = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий от guest_client',
        }
        self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
        )
        self.assertEqual(Comment.objects.count(), comments_count_before)

    def test_correct_adding_comment_in_db(self) -> None:
        """
        When submitting a valid form, add_comment creates a new comment in
        the database.
        """
        comments_count_before = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий от authorized_client',
        }
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data
        )
        self.assertEqual(Comment.objects.count(), comments_count_before + 1)
        created_comment = Comment.objects.latest('id')
        self.assertEqual(created_comment.text, form_data['text'])
        self.assertEqual(created_comment.author, self.author)