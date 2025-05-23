# accounts/views.py

from django.contrib.auth import login, logout, authenticate
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.shortcuts import render, redirect, get_object_or_404
from .forms import CustomUserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.shortcuts import render, redirect
from .forms import CustomUserChangeForm
from recommendations.models import AIRecommendationBook

def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('books:home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/signup.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('books:home')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

@login_required
def mypage_view(request):
    user = request.user
    recommendations = AIRecommendationBook.objects.filter(recommendation__user=user).select_related('book').order_by('-id')[:6]

    return render(request, 'accounts/mypage.html', {
        'recommendations': recommendations
    })

@login_required
def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('books:home')  # 로그아웃 후 홈으로 이동
    return render(request, 'accounts/logout_confirm.html')  # POST 아니면 확인창 띄우기

@login_required
def update(request):
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('accounts:mypage')
    else:
        form = CustomUserChangeForm(instance=request.user)
    return render(request, 'accounts/update.html', {'form': form})


@login_required
def mypage(request):
    return render(request, 'accounts/mypage.html')

@login_required
def userpage_view(request, username):
    User = get_user_model()
    user = get_object_or_404(User, username=username)

    # 본인 마이페이지 접근이면 리다이렉트
    if user == request.user:
        return redirect('accounts:mypage')

    recommendations = AIRecommendationBook.objects.filter(recommendation__user=user).select_related('book').order_by('-id')[:6]

    return render(request, 'accounts/userpage.html', {
        'profile_user': user,
        'recommendations': recommendations
    })