# accounts/views.py

from django.contrib.auth import login, logout, authenticate
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.shortcuts import render, redirect, get_object_or_404
from .forms import CustomUserCreationForm, CustomUserChangeForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from recommendations.models import AIRecommendationBook
from .models import Follow
from libraries.models import Library


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
def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('books:home')
    return render(request, 'accounts/logout_confirm.html')


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
def mypage_view(request):
    user = request.user

    all_recs = AIRecommendationBook.objects.filter(
        recommendation__user=user
    ).select_related('book').order_by('-id')

    seen_ids = set()
    unique_recs = []
    for rec in all_recs:
        if rec.book_id not in seen_ids:
            seen_ids.add(rec.book_id)
            unique_recs.append(rec)
        if len(unique_recs) == 3:
            break

    my_library_books = Library.objects.filter(user=user).values_list('book_id', flat=True)
    my_library_preview = Library.objects.filter(user=user).select_related('book')[:3]

    context = {
        'following_count': user.following.count(),
        'follower_count': user.followers.count(),
        'recommendations': unique_recs,
        'my_library_preview': my_library_preview,
        'my_library_books': list(my_library_books),
        'profile_user': user,
    }
    return render(request, 'accounts/mypage.html', context)


@login_required
def userpage_view(request, username):
    User = get_user_model()
    user = get_object_or_404(User, username=username)

    if user == request.user:
        return redirect('accounts:mypage')

    all_recs = AIRecommendationBook.objects.filter(
        recommendation__user=user
    ).select_related('book').order_by('-id')

    seen_ids = set()
    unique_recs = []
    for rec in all_recs:
        if rec.book_id not in seen_ids:
            seen_ids.add(rec.book_id)
            unique_recs.append(rec)
        if len(unique_recs) == 3:
            break

    is_following = Follow.objects.filter(following_user=request.user, followed_user=user).exists()
    library_preview = Library.objects.filter(user=user).select_related('book')[:3]
    my_library_books = Library.objects.filter(user=request.user).values_list('book_id', flat=True)

    return render(request, 'accounts/userpage.html', {
        'profile_user': user,
        'recommendations': unique_recs,
        'is_following': is_following,
        'library_preview': library_preview,
        'my_library_books': list(my_library_books),
    })


@login_required
def follow_toggle(request, username):
    target_user = get_object_or_404(get_user_model(), username=username)

    if target_user == request.user:
        return JsonResponse({'error': '자기 자신은 팔로우할 수 없습니다.'}, status=400)

    follow_relation = Follow.objects.filter(
        following_user=request.user,
        followed_user=target_user
    ).first()

    if follow_relation:
        follow_relation.delete()
        followed = False
    else:
        Follow.objects.create(
            following_user=request.user,
            followed_user=target_user
        )
        followed = True

    follower_count = Follow.objects.filter(followed_user=target_user).count()

    return JsonResponse({
        'followed': followed,
        'follower_count': follower_count,
    })


@login_required
def follow_list_view(request, username):
    User = get_user_model()
    target_user = get_object_or_404(User, username=username)
    list_type = request.GET.get('type')

    if list_type == 'followers':
        qs = Follow.objects.filter(followed_user=target_user).select_related('following_user')
        users = [rel.following_user for rel in qs]
    else:
        qs = Follow.objects.filter(following_user=target_user).select_related('followed_user')
        users = [rel.followed_user for rel in qs]

    data = []
    for u in users:
        is_following = request.user.following.filter(followed_user_id=u.pk).exists()
        data.append({
            'username': u.username,
            'nickname': u.nickname or u.username,
            'profile_image_url': u.profile_image.url if u.profile_image else '',
            'is_following': is_following
        })

    return JsonResponse({'users': data})
