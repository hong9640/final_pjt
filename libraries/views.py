from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required 
from django.contrib import messages 
from django.core.paginator import Paginator
from django.http import JsonResponse

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


@login_required
def remove_from_library_to_detail(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    user = request.user
    Library.objects.filter(user=user, book=book).delete()
    messages.success(request, f"'{book.title}' 책을 내 서재에서 제거했습니다.")
    return redirect('books:book_detail', book_id=book.id)


@login_required
def remove_from_library_to_mylibrary(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    user = request.user
    Library.objects.filter(user=user, book=book).delete()
    messages.success(request, f"'{book.title}' 책을 내 서재에서 제거했습니다.")
    return redirect('libraries:my_library')


@login_required
def my_library(request):
    user = request.user
    library_qs = Library.objects.filter(user=user).select_related('book')
    
    paginator = Paginator(library_qs, 12)  # 페이지당 12권씩 표시
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'libraries/my_library.html', {
        'page_obj': page_obj
    })


@login_required
def add_to_library_ajax(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    user = request.user
    _, created = Library.objects.get_or_create(user=user, book=book)
    return JsonResponse({'success': created})
