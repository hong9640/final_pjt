from django.urls import path
from . import views

app_name = 'libraries'

urlpatterns = [
    path('add/<int:book_id>/', views.add_to_library, name='add_to_library'),
    path('remove/to-detail/<int:book_id>/', views.remove_from_library_to_detail, name='remove_from_library_to_detail'),
    path('remove/to-library/<int:book_id>/', views.remove_from_library_to_mylibrary, name='remove_from_library_to_mylibrary'),
    path('my-library/', views.my_library, name='my_library'),
    path('add/<int:book_id>/', views.add_to_library, name='add_to_library'),
    path('add/ajax/<int:book_id>/', views.add_to_library_ajax, name='add_to_library_ajax'),
]
