from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import MAX_NUMBER_CHARS_IN_POST_PRESENTATION, Group, Post

User = get_user_model()


class PostModelTests(TestCase):
    """Checking that post model is working correctly."""

    @classmethod
    def setUpClass(cls) -> None:
        """Preparing for tests."""
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_posts_have_correct_object_names(self) -> None:
        """Checking that __str__ is working correctly for posts."""
        self.assertEqual(
            PostModelTests.post.__str__(),
            PostModelTests.post.text[:MAX_NUMBER_CHARS_IN_POST_PRESENTATION]
        )

    def test_posts_verbose_name(self) -> None:
        """
        Checking that the verbose_name in the post fields matches what is
        expected.
        """
        post = PostModelTests.post
        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value)

    def test_posts_help_text(self) -> None:
        """
        Checking that the help_text in the post fields matches what is
        expected.
        """
        post = PostModelTests.post
        field_help_texts = {
            'text': 'Введите текст поста',
            'pub_date': 'Введите дату публикации',
            'author': 'Укажите автора',
            'group': 'Группа, к которой будет относиться пост',
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value)


class GroupModelTests(TestCase):
    """Checking that group model is working correctly."""

    @classmethod
    def setUpClass(cls) -> None:
        """Preparing for tests."""
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )

    def test_groups_have_correct_object_names(self) -> None:
        """Checking that __str__ is working correctly for groups."""
        self.assertEqual(GroupModelTests.group.__str__(),
                         GroupModelTests.group.title)

    def test_groups_verbose_name(self) -> None:
        """
        Checking that the verbose_name in the group fields matches what is
        expected.
        """
        group = GroupModelTests.group
        field_verboses = {
            'title': 'Название группы',
            'slug': 'Адрес для страницы с группой',
            'description': 'Описание группы',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    group._meta.get_field(field).verbose_name, expected_value)

    def test_groups_help_text(self) -> None:
        """
        Checking that the help_text in the group fields matches what is
        expected.
        """
        group = GroupModelTests.group
        field_help_text = {
            'title': 'Введите название группы',
            'slug': ('Укажите адрес для страницы задачи. Используйте только '
                     'латиницу, цифры, дефисы и знаки подчёркивания'),
            'description': 'Введите описание группы',
        }
        for field, expected_value in field_help_text.items():
            with self.subTest(field=field):
                self.assertEqual(
                    group._meta.get_field(field).help_text, expected_value)
