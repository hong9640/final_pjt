from django.db import models

# Create your models here.

from django.db import models

class Author(models.Model):
    name = models.CharField(max_length=255)
    profile_image = models.URLField(blank=True, null=True)
    biography = models.TextField(blank=True)

class Category(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    isbn13 = models.CharField(max_length=13, unique=True)
    description = models.TextField(blank=True)
    cover_image_url = models.URLField(blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    pub_date = models.CharField(max_length=20)
    link = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
