# books/views.py
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import Book, Category, Author
from libraries.models import Library
from reviews.models import Review, Like
from reviews.forms import ReviewForm, CommentForm
import re
from collections import defaultdict

CATEGORY_GROUPS = [
    "문학/소설", "어린이/청소년", "만화/웹툰",
    "인문/사회", "자기계발/경제", "건강/취미",
    "교육/수험서", "기타"
]

def extract_second_level(name):
    parts = name.split(">")
    return parts[1].strip() if len(parts) > 1 else name.strip()

def classify_category_group(second_level):
    group_map = {
        "문학/소설": ["소설", "시", "희곡", "장르소설", "문학"],
        "어린이/청소년": ["어린이", "초등", "청소년"],
        "만화/웹툰": ["만화", "웹툰", "라이트노벨"],
        "인문/사회": ["인문", "철학", "역사", "사회", "종교", "정치", "심리"],
        "자기계발/경제": ["자기계발", "경제", "경영", "투자", "재테크", "비즈니스"],
        "건강/취미": ["건강", "취미", "요리", "여행", "스포츠", "반려동물"],
        "교육/수험서": ["수험서", "자격증", "교재", "외국어", "컴퓨터", "IT", "학습"],
    }
    for group, keywords in group_map.items():
        if any(keyword in second_level for keyword in keywords):
            return group
    return "기타"

def home(request):
    query = request.GET.get('q', None)
    context = {
        'query': query,
        # global_categories는 검색 결과가 아닐 때만 필요하므로, 아래에서 조건부로 추가
    }

    if query:
        # 검색어가 있으면, 전체 책을 대상으로 검색
        searched_books = Book.objects.filter(title__icontains=query).order_by('-pub_date') # 최신순 정렬 또는 원하는 정렬 방식
        context['searched_books'] = searched_books
        context['page_title'] = f"'{query}' 검색 결과" # 검색 결과 페이지 제목
        # 검색 결과 페이지에서는 sticky_category_nav가 표시되지 않으므로 global_categories 불필요
    else:
        # 검색어가 없으면, 기존 홈 페이지 로직 수행
        bestseller_books_qs = Book.objects.filter(is_bestseller=True).select_related('category')
        grouped_bestsellers = defaultdict(list)
        for book in bestseller_books_qs:
            if book.category:
                second_level = extract_second_level(book.category.name)
                group = classify_category_group(second_level)
            else:
                group = "기타"
            grouped_bestsellers[group].append(book)

        new_books_qs = Book.objects.order_by('-pub_date')[:6]

        context.update({
            'grouped_bestsellers': dict(grouped_bestsellers),
            'category_groups': CATEGORY_GROUPS, # 베스트셀러 탭 이름용
            'bestseller_groups': list(grouped_bestsellers.keys()),
            'new_books': new_books_qs,
            'global_categories': get_navigation_categories(), # 상단 네비게이션 바용
            'page_title': "홈", # 기본 홈 페이지 제목
        })

    return render(request, 'books/home.html', context)


def bestseller_api(request):
    category_id = request.GET.get("category_id")
    books = Book.objects.filter(category_id=category_id, is_bestseller=True)[:6]
    data = { "books": [ { "title": book.title, "cover_image_url": book.cover_image_url, } for book in books ] }
    return JsonResponse(data)

def extract_primary_author_name(raw_author_str):
    first = raw_author_str.split(',')[0].strip()
    cleaned = re.sub(r'\s*\([^)]*\)', '', first).strip()
    return cleaned

def book_detail(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    author = getattr(book, 'author', None)

    # 저자명 정제 로직
    if author and isinstance(author.name, str):
        clean_author_name = re.sub(r'\s*\([^)]*\)', '', author.name.split(',')[0].strip())
    elif author:
        clean_author_name = str(author.name) if author.name else "정보 없음"
    else:
        clean_author_name = "정보 없음"

    # 로그인 사용자 보유 여부
    is_in_library = False
    if request.user.is_authenticated:
        is_in_library = Library.objects.filter(user=request.user, book=book).exists()

    # 리뷰 목록, 좋아요 여부, 댓글 목록 처리
    book_reviews_qs = book.reviews.select_related('user').prefetch_related(
        'comments__user',
        'likes_received'
    ).order_by('-created_at')

    reviews_with_details = []
    liked_ids = set()
    if request.user.is_authenticated:
        liked_ids = set(
            Like.objects.filter(user=request.user, review__in=book_reviews_qs)
            .values_list('review_id', flat=True)
        )

    for review in book_reviews_qs:
        reviews_with_details.append({
            'review_obj': review,
            'like_count': review.likes_received.count(),
            'user_has_liked': review.id in liked_ids,
            'comments_list': review.comments.all().order_by('created_at'),
        })

    context = {
        'book': book,
        'author': author,
        'clean_author_name': clean_author_name,
        'is_in_library': is_in_library,
        'reviews_with_details': reviews_with_details,
        'review_form': ReviewForm(),
        'comment_form': CommentForm(),
        'global_categories': get_navigation_categories(),
        'category_groups': CATEGORY_GROUPS,
    }
    return render(request, 'books/book_detail.html', context)


def all_books_list(request):
    book_list_qs = Book.objects.all().order_by('-pub_date')
    paginator = Paginator(book_list_qs, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_title': "전체 도서",
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'global_categories': get_navigation_categories(),
        'category_groups': CATEGORY_GROUPS,
    }
    return render(request, 'books/category_total.html', context)

def books_by_category_view(request, category_id):
    clicked_category_object = get_object_or_404(Category, id=category_id)
    processed_name = clicked_category_object.name.strip().rstrip('>')
    name_parts = processed_name.split('>')
    key_name_part = name_parts[1].strip() if len(name_parts) > 1 else name_parts[0].strip()
    display_name_for_title = key_name_part
    filter_keyword = key_name_part

    relevant_categories = Category.objects.filter(name__icontains=filter_keyword)
    book_list_for_category = Book.objects.filter(category__in=relevant_categories).order_by('-pub_date').distinct()

    paginator = Paginator(book_list_for_category, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'current_category': clicked_category_object,
        'page_title': display_name_for_title,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'global_categories': get_navigation_categories(),
    }
    return render(request, 'books/category.html', context)

def get_navigation_categories():
    categories_qs = Category.objects.filter(name__startswith="국내도서>")
    nav_list = []
    seen_categories = set()
    for cat in categories_qs:
        parts = cat.name.split(">")
        if len(parts) > 1:
            second_level_name = parts[1].strip()
            if second_level_name not in seen_categories:
                seen_categories.add(second_level_name)
                nav_list.append({ 'id': cat.id, 'name': second_level_name })
            if len(nav_list) >= 6:
                break
    return nav_list

def books_by_group_view(request, group_name):
    def normalize(s): return s.strip().replace(" ", "").lower()
    group_name = group_name.replace("-", "/")
    normalized_target = normalize(group_name)

    all_books = Book.objects.select_related('category').order_by('-pub_date')
    filtered_books = []
    for book in all_books:
        if book.category:
            second = extract_second_level(book.category.name)
            group = classify_category_group(second)
            if normalize(group) == normalized_target:
                filtered_books.append(book)

    paginator = Paginator(filtered_books, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_title': group_name,
        'current_group': group_name,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'global_categories': get_navigation_categories(),
        'category_groups': CATEGORY_GROUPS,
    }
    return render(request, 'books/category.html', context)