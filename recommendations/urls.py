from django.urls import path
from . import views

app_name = 'recommendations'

urlpatterns = [
    path('recommend/', views.get_recommendation, name='get_recommendation'),
]
