from django import forms

from .models import Comment, Group, Post


class PostForm(forms.ModelForm):
    """
    Form for creating and editing posts.

    Fields:
        text (TextField): The text of the post.
        group (ModelChoiceField): Optional parameter to specify which group
            the post belongs to.
    """

    group = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=False,
        label='Группа',
        help_text='Группа, к которой будет относиться пост',
    )

    class Meta:
        model = Post
        fields = ('text', 'group', 'image')


class CommentForm(forms.ModelForm):
    """
    Form for adding comments to posts.

    Fields:
        text (TextField): Comment text.
    """

    class Meta:
        model = Comment
        fields = ('text',)
