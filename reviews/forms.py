# reviews/forms.py
from django import forms
from .models import Review, Comment

class ReviewForm(forms.ModelForm):
    rating = forms.IntegerField(
        min_value=1, # Min value for rating
        max_value=5, # Max value for rating
        widget=forms.HiddenInput(attrs={'id': 'id_rating_hidden'}),
        required=True, # Ensure rating is required
        error_messages={'required': '별점을 선택해주세요.'} # Server-side error message
    )

    class Meta:
        model = Review
        fields = ['rating', 'content']
        widgets = {
            'content': forms.Textarea(attrs={
                'placeholder': '이 책에 대한 생각을 자유롭게 공유해주세요. (예: 인상 깊었던 구절, 추천 이유 등)',
                'rows': 3, # Adjusted rows for a more compact form initially
                'id': 'reviewTextarea',
                'class': 'w-full p-2 border rounded-md focus:ring-blue-500 focus:border-blue-500',
            }),
        }
        labels = {
            'content': '리뷰 내용',
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': '댓글을 입력하세요...',
                'class': 'w-full p-2 border rounded-md focus:ring-blue-500 focus:border-blue-500 text-sm'
            }),
        }
        labels = {
            'content': '', # Hide label for a cleaner look if placeholder is enough
        }
