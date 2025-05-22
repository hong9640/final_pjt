from django.urls import path
from . import views


app_name='books'
urlpatterns = [
    path('', views.home, name='home'),
    # path('book/<int:book_id>/', views.book_detail, name='book_detail'),
    # path('category/<int:category_id>/', views.books_category, name='books_category'),
    # path('author/<int:author_id>/', views.author_detail, name='author_detail'),
    path("api/bestsellers/", views.bestseller_api, name="bestseller_api"),
]