# accounts/urls.py

from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('mypage/', views.mypage_view, name='mypage'),
    path('update/', views.update, name='update'),
    path('user/<str:username>/', views.userpage_view, name='userpage'),
    path('follow/<str:username>/', views.follow_toggle, name='follow_toggle'),
    path('ajax/follow_list/<str:username>/', views.follow_list_view, name='follow_list'),
]
