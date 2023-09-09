from django import forms
from django.core.validators import MinValueValidator

from .models import Comments, Reply


class CommentsForm(forms.ModelForm):
    class Meta:
        model = Comments
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control'}),
        }

    def clean_text(self):
        text = self.cleaned_data['text']
        return text


class ReplyForm(forms.ModelForm):
    class Meta:
        model = Reply
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),  # Adjust 'rows' as needed
        }

    def clean_text(self):
        text = self.cleaned_data['text']
        return text

