from django.http import JsonResponse
from django.core.paginator import Paginator
from django.shortcuts import render
from .models import Category, Book, Author
from django.shortcuts import render, get_object_or_404

def home(request):
    categories_qs = Category.objects.filter(name__startswith="국내도서>")
    
    second_levels = []
    seen = set()
    for cat in categories_qs:
        parts = cat.name.split(">")
        if len(parts) > 1:
            second = parts[1].strip()
            if second not in seen:
                seen.add(second)
                second_levels.append({'name': second, 'display_name': second, 'id': cat.id})
            if len(second_levels) >= 6:
                break

    bestseller_books = Book.objects.filter(is_bestseller=True).select_related('category')[:6]
    new_books = Book.objects.order_by('-pub_date')[:6]

    context = {
        'categories': second_levels,
        'bestseller_books': bestseller_books,
        'new_books': new_books,
    }
    return render(request, 'books/home.html', context)

def bestseller_api(request):
    category_id = request.GET.get("category_id")
    books = Book.objects.filter(category_id=category_id, is_bestseller=True)[:6]
    data = {
        "books": [
            {
                "title": book.title,
                "cover_image_url": book.cover_image_url,
            } for book in books
        ]
    }
    return JsonResponse(data)


def book_detail(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    # Book 모델에 'author' 필드가 ForeignKey 또는 OneToOneField로 연결되어 있다고 가정합니다.
    # author 정보가 필요 없다면 아래 author 변수 및 context에서 제거해도 됩니다.
    author = getattr(book, 'author', None) # author 필드가 없을 수도 있으니 getattr 사용

    # book_detail.html에서 사용할 리뷰 데이터 (아직 review 앱이 없으므로 빈 리스트 또는 샘플)
    sample_reviews = [
        {
            'user': {'username': '김샘플', 'reading_type': '분석형'},
            'rating': 4,
            'content': '샘플 리뷰입니다. 책 내용이 아주 유익했어요.',
            'created_at': '2025-05-20 10:00:00', # datetime 객체로 전달하는 것이 좋음
            'category': 'IT',
        },
    ]

    context = {
        'book': book,
        'author': author, # book_detail.html 에서 {{ author }} 또는 {{ book.author }} 로 접근
        'reviews': sample_reviews, # book_detail.html에 reviews 변수 전달
    }
    return render(request, 'books/book_detail.html', context)

def books_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    book_list = Book.objects.filter(category=category).order_by('-pub_date')

    paginator = Paginator(book_list, 9) # 한 페이지에 9권씩 (3x3 그리드)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'current_category': category,       # 현재 보고 있는 주 카테고리 객체
        'page_obj': page_obj,               # 페이징된 책 목록
        'is_paginated': page_obj.has_other_pages(),
        # 'categories_for_nav' 와 같은 네비게이션 바용 카테고리 목록 전달 로직 제거
    }
    return render(request, 'books/category_total.html', context)


