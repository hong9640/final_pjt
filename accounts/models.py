
# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings


class User(AbstractUser):
    email = models.EmailField(unique=True)
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)  # 수정됨
    nickname = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username


class Follow(models.Model):
    following_user = models.ForeignKey(User, related_name='following', on_delete=models.CASCADE)
    followed_user = models.ForeignKey(User, related_name='followers', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
class BookProfileCard(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reading_card'
    )
    title = models.CharField(max_length=100, help_text="카드 제목")
    
    # ✅ 고정 장르 선택을 위한 JSONField
    favorite_genres = models.JSONField(default=list)

    reading_style = models.CharField(max_length=100, blank=True)
    reading_time = models.CharField(max_length=50, blank=True)
    reading_place = models.CharField(max_length=100, blank=True)
    mood = models.CharField(max_length=100, blank=True)
    introduction = models.TextField(blank=True)
    
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}님의 독서 카드"