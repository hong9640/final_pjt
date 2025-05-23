# libraries/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required 
from django.contrib import messages 
from .models import Library        
from books.models import Book     

@login_required
def add_to_library(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    user = request.user
    library_entry, created = Library.objects.get_or_create(user=user, book=book)

    if created:
        messages.success(request, f"'{book.title}' 책을 내 서재에 추가했습니다.")
    else:
        messages.info(request, f"'{book.title}' 책은 이미 내 서재에 있습니다.")

    return redirect('books:book_detail', book_id=book.id)

@login_required # 👈 "제거" 기능 뷰 함수 추가
def remove_from_library(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    user = request.user

    library_entry = Library.objects.filter(user=user, book=book)

    if library_entry.exists():
        library_entry.delete()
        messages.success(request, f"'{book.title}' 책을 내 서재에서 제거했습니다.")
    else:
        messages.warning(request, f"'{book.title}' 책이 내 서재에 없거나 이미 제거되었습니다.")

    return redirect('books:book_detail', book_id=book.id)