# accounts/urls.py

from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .forms import CustomPasswordChangeForm

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
    path('password_change/', auth_views.PasswordChangeView.as_view(
        template_name='accounts/password_change.html',
        success_url='/accounts/mypage/',
        form_class=CustomPasswordChangeForm,
    ), name='password_change'),
    path('book-card/', views.book_profile_card_view, name='book_profile_card'),
]
