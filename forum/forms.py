from django import forms
from .models import Post, Comment


from django import forms
from .models import Post

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content', 'media']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter post title'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Write your post content here'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['media'].widget.attrs.update({'class': 'form-control-file'})

    def clean_media(self):
        media = self.cleaned_data.get('media')

        if media:
            # Validate file type
            allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'mp4', 'mov']
            file_extension = media.name.split('.')[-1].lower()
            if file_extension not in allowed_extensions:
                raise forms.ValidationError("Only image or video files (JPG, PNG, GIF, MP4, MOV) are allowed.")

            # Validate file size (limit to 10MB)
            max_file_size = 10 * 1024 * 1024  # 10MB
            if media.size > max_file_size:
                raise forms.ValidationError("File size must not exceed 10MB.")

        return media




class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content', 'media', 'parent_comment']
        widgets = {
            'content': forms.Textarea(attrs={'placeholder': 'Write your comment...'}),
        }





