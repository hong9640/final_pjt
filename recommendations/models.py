from django.db import models

# Create your models here.
from django.db import models
from accounts.models import User
from books.models import Book

class AIRecommendation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    input_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class AIRecommendationBook(models.Model):
    recommendation = models.ForeignKey(AIRecommendation, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    explanation = models.TextField()
