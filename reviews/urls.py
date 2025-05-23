# reviews/urls.py
from django.urls import path
from . import views

app_name = 'reviews'  # ✨ 이 줄이 매우 중요합니다!

urlpatterns = [
    # Path for adding a review to a book
    path('book/<int:book_id>/add/', views.add_review, name='add_review'),
    # Path for liking/unliking a review
    path('<int:review_id>/like/', views.like_review, name='like_review'),
    # Path for deleting a review
    path('<int:review_id>/delete/', views.delete_review, name='delete_review'),
    # Path for adding a comment to a review
    path('<int:review_id>/comment/add/', views.add_comment, name='add_comment'),
    # Path for deleting a comment
    path('comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
]