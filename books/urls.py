from django.urls import path
from . import views


app_name='books'
urlpatterns = [
    path('', views.home, name='home'),
    path('book/<int:book_id>/', views.book_detail, name='book_detail'),
    path('all/', views.all_books_list, name='all_books_list'),
    # path('category/<int:category_id>/', views.category_total, name='category_total'),
    # path('author/<int:author_id>/', views.author_detail, name='author_detail'),
    path("api/bestsellers/", views.bestseller_api, name="bestseller_api"),
    path('category/<int:category_id>/', views.books_by_category_view, name='books_by_category'),
]