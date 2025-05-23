from django.http import JsonResponse
from django.core.paginator import Paginator
from django.shortcuts import render
from .models import Category, Book, Author
from django.shortcuts import render, get_object_or_404
import re

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

def extract_primary_author_name(raw_author_str):
    """
    "황석희 (지은이), 홍길동 (옮긴이)" → "황석희"
    "무라카미 하루키 (지은이)" → "무라카미 하루키"
    "정유정" → "정유정"
    """
    # ① 쉼표로 분할 후 첫 번째만 사용
    first = raw_author_str.split(',')[0].strip()

    # ② 괄호 제거
    cleaned = re.sub(r'\s*\([^)]*\)', '', first).strip()
    return cleaned



def book_detail(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    author = getattr(book, 'author', None)

    if author and author.name:
        clean_author_name = extract_primary_author_name(author.name)
    else:
        clean_author_name = ''

    # 샘플 리뷰
    sample_reviews = [
        {
            'user': {'username': '김샘플', 'reading_type': '분석형'},
            'rating': 4,
            'content': '샘플 리뷰입니다. 책 내용이 아주 유익했어요.',
            'created_at': '2025-05-20 10:00:00',
            'category': 'IT',
        },
    ]

    context = {
        'book': book,
        'author': author,
        'clean_author_name': clean_author_name,  # 템플릿에 전달
        'reviews': sample_reviews,
    }
    return render(request, 'books/book_detail.html', context)


def all_books_list(request):
    """
    모든 책 목록을 보여주는 뷰 (페이지네이션 포함)
    category_total.html 템플릿을 재활용합니다.
    """
    # --- 네비게이션용 카테고리 목록 생성 (views.home에서 가져온 로직) ---
    categories_qs_nav = Category.objects.filter(name__startswith="국내도서>") # 변수명 _nav 추가하여 구분
    nav_categories_list = []
    seen_nav_categories = set()
    for cat_nav in categories_qs_nav: # 변수명 cat_nav 사용
        parts = cat_nav.name.split(">")
        if len(parts) > 1:
            second_level_name = parts[1].strip()
            if second_level_name not in seen_nav_categories:
                seen_nav_categories.add(second_level_name)
                nav_categories_list.append({
                    'id': cat_nav.id,
                    'name': second_level_name,
                    'display_name': second_level_name # home 뷰와 일관성을 위해 추가
                })
            if len(nav_categories_list) >= 6: # 최대 6개
                break
    # --- 네비게이션용 카테고리 목록 생성 끝 ---

    book_list_qs = Book.objects.all().order_by('-pub_date')

    paginator = Paginator(book_list_qs, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_title': "전체 도서",
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'categories': nav_categories_list, # <<< 'categories'를 컨텍스트에 추가!
    }
    return render(request, 'books/category_total.html', context)
