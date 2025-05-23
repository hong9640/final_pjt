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
    
    # sticky_category_nav.html이 사용하는 category_groups와
    # 다른 곳에서 사용할 수 있는 global_categories를 항상 컨텍스트에 포함합니다.
    # sticky_category_nav.html이 category_groups (CATEGORY_GROUPS 리스트)를 사용하므로 이를 전달합니다.
    context = {
        'query': query,
        'global_categories': get_navigation_categories(), # 사용자님의 get_navigation_categories 함수 사용
        'category_groups': CATEGORY_GROUPS, # sticky_category_nav.html이 순회하는 대상
    }

    if query:
        # 검색어가 있으면, 전체 책을 대상으로 검색
        searched_books = Book.objects.filter(title__icontains=query).order_by('-pub_date')
        context['searched_books'] = searched_books
        context['page_title'] = f"'{query}' 검색 결과"
        # 검색 결과 페이지에서는 기존 홈 콘텐츠(베스트셀러, 신간 등)는 전달하지 않음
        # 'category_groups'는 이미 context 상단에 추가됨
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

        # context.update를 사용하여 기존 context에 추가 (query, global_categories, category_groups는 유지됨)
        context.update({
            'grouped_bestsellers': dict(grouped_bestsellers),
            # 'category_groups': CATEGORY_GROUPS, # 이미 context 상단에 추가됨
            'bestseller_groups': list(grouped_bestsellers.keys()), # 베스트셀러 탭 내부에서 사용
            'new_books': new_books_qs,
            'page_title': "홈", 
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
    query = request.GET.get('q')
    book_list_qs = Book.objects.all().order_by('-pub_date')

    page_title_display = "전체 도서"
    if query:
        book_list_qs = book_list_qs.filter(title__icontains=query)
        page_title_display = f"'{query}' 검색 결과 (전체 도서)"

    paginator = Paginator(book_list_qs, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_title': page_title_display,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'global_categories': get_navigation_categories(), # 네비게이션 바 데이터
        'category_groups': CATEGORY_GROUPS,             # 네비게이션 바 데이터
        'query': query,
    }
    return render(request, 'books/category_total.html', context)

def books_by_category_view(request, category_id):
    query = request.GET.get('q')
    clicked_category_object = get_object_or_404(Category, id=category_id)

    processed_name = clicked_category_object.name.strip().rstrip('>')
    name_parts = processed_name.split('>')
    key_name_part = name_parts[1].strip() if len(name_parts) > 1 else name_parts[0].strip()
    
    # 기본 페이지 제목은 현재 카테고리 이름
    page_title_display = key_name_part

    # 해당 카테고리(또는 관련된 카테고리 그룹)의 책 목록 가져오기
    # 여기서는 clicked_category_object의 이름을 포함하는 모든 카테고리의 책을 가져옵니다.
    # 만약 정확히 해당 category_id에 속한 책만 보여주려면 필터링 로직을 수정해야 합니다.
    relevant_categories = Category.objects.filter(name__icontains=key_name_part) # filter_keyword 대신 key_name_part 사용
    book_list_for_category = Book.objects.filter(category__in=relevant_categories).order_by('-pub_date').distinct()

    if query:
        book_list_for_category = book_list_for_category.filter(title__icontains=query)
        page_title_display = f"'{query}' 검색 결과 ({key_name_part})" # 검색 시 페이지 제목 변경

    paginator = Paginator(book_list_for_category, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'current_category_object': clicked_category_object, # 현재 카테고리 객체 (URL 생성 등에 사용)
        'page_title': page_title_display,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'global_categories': get_navigation_categories(), # 네비게이션 바 데이터
        'category_groups': CATEGORY_GROUPS,             # 네비게이션 바 데이터
        'query': query,
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

def books_by_group_view(request, group_name): # URL의 group_name은 슬러그 (예: 문학-소설)
    query = request.GET.get('q')

    actual_group_display_name = group_name # 기본값
    for cat_group_in_list in CATEGORY_GROUPS:
        if cat_group_in_list.replace("/", "-").lower() == group_name.lower():
            actual_group_display_name = cat_group_in_list
            break
    if group_name.lower() == "기타": # URL 슬러그가 '기타'인 경우
        actual_group_display_name = "기타"

    # 해당 그룹의 책 필터링
    all_books = Book.objects.select_related('category').order_by('-pub_date')
    filtered_books_for_this_group = []
    for book in all_books:
        book_group_classified = "기타" # 기본 그룹
        if book.category:
            second_level = extract_second_level(book.category.name)
            book_group_classified = classify_category_group(second_level)
        
        if book_group_classified == actual_group_display_name:
            filtered_books_for_this_group.append(book)
    
    page_title_display = actual_group_display_name
    if query:
        filtered_books_for_this_group = [
            book for book in filtered_books_for_this_group 
            if query.lower() in book.title.lower()
        ]
        page_title_display = f"'{query}' 검색 결과 ({actual_group_display_name})"

    paginator = Paginator(filtered_books_for_this_group, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_title': page_title_display,
        'current_group_slug': group_name, # 검색 폼 action URL 생성용
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'global_categories': get_navigation_categories(), # 네비게이션 바 데이터
        'category_groups': CATEGORY_GROUPS,             # 네비게이션 바 데이터
        'query': query,
    }
    return render(request, 'books/category.html', context)