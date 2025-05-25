# reviews/models.py
from django.db import models
from django.conf import settings
from books.models import Book, Category # Category 모델도 임포트합니다.
from django.urls import reverse

class Review(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews_written')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField()  # 예: 1-5
    content = models.TextField()
    
    # 책의 카테고리 이름을 저장할 필드 (자동으로 채워짐)
    book_category_at_review = models.CharField(max_length=100, blank=True, null=True, verbose_name="책 카테고리")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at'] # 최신 리뷰가 먼저 오도록
        # unique_together = ('user', 'book') # 선택: 사용자가 책당 하나의 리뷰만 작성하도록 제한

    def __str__(self):
        return f"리뷰: {self.content[:20]} (작성자: {self.user.username}, 책: {self.book.title})"
    
    def get_book_detail_url(self):
        # books 앱의 book_detail URL name과 book.id를 사용하여 URL을 생성합니다.
        return reverse('books:book_detail', kwargs={'book_id': self.book.pk})

# Comment 및 Like 모델은 기존과 동일하게 유지 (추후 기능 구현 시 사용)
class Comment(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='review_comments_written')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"댓글: {self.content[:20]} (작성자: {self.user.username})"

class Like(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='review_likes_given')
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='likes_received')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'review')

    def __str__(self):
        return f"{self.user.username} likes review (ID: {self.review.id})"