# reviews/forms.py
from django import forms
from .models import Review

class ReviewForm(forms.ModelForm):
    rating = forms.IntegerField(
        min_value=1,
        max_value=5,
        widget=forms.HiddenInput(attrs={'id': 'id_rating_hidden'}) # JS와 연동
    )

    class Meta:
        model = Review
        fields = ['rating', 'content'] # 'book_category_at_review'는 폼에서 제외
        widgets = {
            'content': forms.Textarea(attrs={
                'placeholder': '이 책에 대한 생각을 자유롭게 공유해주세요. (예: 인상 깊었던 구절, 추천 이유 등)',
                'rows': 4,
                'id': 'reviewTextarea',
                'style': 'width: calc(100% - 1rem); margin-bottom: 1rem;',
            }),
        }
        labels = {
            'content': '리뷰 내용',
        }