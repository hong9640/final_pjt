from django.urls import path
from . import views


app_name='books'
urlpatterns = [
    path('', views.home, name='home'),
    path('book/<int:book_id>/', views.book_detail, name='book_detail'),
    path('all/', views.all_books_list, name='all_books_list'),
    path("api/bestsellers/", views.bestseller_api, name="bestseller_api"),
    path('category/<int:category_id>/', views.books_by_category_view, name='books_by_category'),
    path('group/<str:group_name>/', views.books_by_group_view, name='books_by_group'),
]