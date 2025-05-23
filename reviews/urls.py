# reviews/urls.py
from django.urls import path
from . import views

app_name = 'reviews'  # ✨ 이 줄이 매우 중요합니다!

urlpatterns = [
    path('book/<int:book_id>/add/', views.add_review, name='add_review'),
    # 다른 URL 패턴이 있다면 여기에 추가
]