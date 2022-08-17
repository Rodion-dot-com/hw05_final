from django.contrib.auth import get_user_model
from django.db import models

MAX_CHAR_FIELD_SIZE = 200
MAX_NUMBER_CHARS_IN_POST_PRESENTATION = 15
MAX_NUMBER_CHARS_IN_COMMENT_PRESENTATION = 10

User = get_user_model()


class Group(models.Model):
    """
    Model for storing groups.

    Fields:
        title (CharField): The name of the group.
        slug (SlugField): The unique address of the group, part of the URL.
        description (TextField): A text describing the community.
            This text will be displayed on the community page.
    """

    title = models.CharField(
        max_length=MAX_CHAR_FIELD_SIZE,
        verbose_name='Название группы',
        help_text='Введите название группы',
    )
    slug = models.SlugField(
        unique=True,
        verbose_name='Адрес для страницы с группой',
        help_text=('Укажите адрес для страницы задачи. Используйте только '
                   'латиницу, цифры, дефисы и знаки подчёркивания'),
    )
    description = models.TextField(
        verbose_name='Описание группы',
        help_text='Введите описание группы',
    )

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'

    def __str__(self):
        return self.title


class Post(models.Model):
    """
    Model for storing posts.

    Fields:
        text (TextField): The text of the post.
        pub_date (DateTimeField): Date of publication of the post.
        author (ForeignKey): Indicates the author of the post.
        group (ForeignKey): Indicates the group of the post.
        image (ImageField): Image for the post.
    """

    text = models.TextField(verbose_name='Текст поста',
                            help_text='Введите текст поста',)
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации',
        help_text='Введите дату публикации',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор',
        help_text='Укажите автора',
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='posts',
        verbose_name='Группа',
        help_text='Группа, к которой будет относиться пост',
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'

    def __str__(self):
        return self.text[:MAX_NUMBER_CHARS_IN_POST_PRESENTATION]


class Comment(models.Model):
    """
    Model for storing comments.

    Fields:
        post (ForeignKey): Link to the post to which the comment was left.
        author (ForeignKey): Link to the author of the comment.
        text (TextField): Comment text.
        created (DateTimeField): Automatically substituted date and time of
            publication of the comment.
    """

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Пост'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор'
    )
    text = models.TextField(
        verbose_name='Текст комментария',
        help_text='Введите текст комментария'
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации',
    )

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return self.text[:MAX_NUMBER_CHARS_IN_COMMENT_PRESENTATION]


class Follow(models.Model):
    """
    A model for storing subscription information.

    Fields:
        user (ForeignKey): Link to the user object who subscribes.
        author (ForeignKey): Link to the user object to subscribe to.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following'
    )

    def __str__(self):
        return f'{self.user.username} follows {self.author.username}'
