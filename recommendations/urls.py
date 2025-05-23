# recommendations/urls.py
from django.urls import path
from . import views

app_name = 'recommendations'

urlpatterns = [
    path('recommend/', views.get_recommendation, name='get_recommendation'),
    path('recommend/ajax/', views.get_recommendation_ajax, name='get_recommendation_ajax'),
    path('result/', views.show_result, name='show_result'),
]
