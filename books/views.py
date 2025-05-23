# books/views.py (계속)
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import Book, Category, Author
from libraries.models import Library
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
    bestseller_books = Book.objects.filter(is_bestseller=True).select_related('category')
    grouped_bestsellers = defaultdict(list)
    for book in bestseller_books:
        if book.category:
            second_level = extract_second_level(book.category.name)
            group = classify_category_group(second_level)
        else:
            group = "기타"
        grouped_bestsellers[group].append(book)

    new_books = Book.objects.order_by('-pub_date')[:6]

    context = {
        'grouped_bestsellers': dict(grouped_bestsellers),
        'category_groups': CATEGORY_GROUPS,
        'bestseller_groups': list(grouped_bestsellers.keys()),  # home.html 필터용
        'new_books': new_books,
        'global_categories': CATEGORY_GROUPS,
    }
    return render(request, 'books/home.html', context)


def bestseller_api(request): # 이 뷰는 템플릿을 직접 렌더링하지 않으므로 수정 불필요
    category_id = request.GET.get("category_id")
    books = Book.objects.filter(category_id=category_id, is_bestseller=True)[:6]
    data = { "books": [ { "title": book.title, "cover_image_url": book.cover_image_url, } for book in books ] }
    return JsonResponse(data)

def extract_primary_author_name(raw_author_str):
    """
    "황석희 (지은이), 홍길동 (옮긴이)" → "황석희"
    "무라카미 하루키 (지은이)" → "무라카미 하루키"
    "정유정" → "정유정"
    """
    first = raw_author_str.split(',')[0].strip()
    cleaned = re.sub(r'\s*\([^)]*\)', '', first).strip()
    return cleaned


def book_detail(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    author = getattr(book, 'author', None)

    # author name 정제
    if author and author.name:
        clean_author_name = extract_primary_author_name(author.name)
    else:
        clean_author_name = ''

    # 로그인 사용자 도서 보유 여부
    is_in_library = False
    if request.user.is_authenticated:
        if Library.objects.filter(user=request.user, book=book).exists():
            is_in_library = True

    # 샘플 리뷰 데이터
    sample_reviews = [
        {
            'user': {'username': '김샘플', 'reading_type': '분석형'},
            'rating': 4,
            'content': '샘플 리뷰입니다. 책 내용이 아주 유익했어요.',
            'created_at': '2025-05-20 10:00:00',
            'category': 'IT',
        },
    ]

    # 고정 네비게이션 바용 카테고리
    nav_categories_for_sticky_bar = get_navigation_categories()

    context = {
        'book': book,
        'author': author,
        'clean_author_name': clean_author_name,
        'reviews': sample_reviews,
        'is_in_library': is_in_library,
        'global_categories': nav_categories_for_sticky_bar,
        'category_groups': CATEGORY_GROUPS
    }
    return render(request, 'books/book_detail.html', context)

def all_books_list(request):
    """
    모든 책 목록을 보여주는 뷰 (페이지네이션 포함)
    category_total.html 템플릿을 재활용합니다.
    """
    # sticky_category_nav.html을 위한 카테고리 목록
    nav_categories_for_sticky_bar = get_navigation_categories() # 헬퍼 함수 사용

    book_list_qs = Book.objects.all().order_by('-pub_date')
    paginator = Paginator(book_list_qs, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_title': "전체 도서",
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'global_categories': nav_categories_for_sticky_bar, # 고정 네비게이션 바용
        'category_groups': CATEGORY_GROUPS,
    }
    return render(request, 'books/category_total.html', context)

def books_by_category_view(request, category_id):
    """
    특정 카테고리 ID를 기반으로, 해당 카테고리 이름(또는 주요 부분)을 포함하는
    모든 카테고리의 책 목록을 페이지네이션하여 보여줍니다.
    페이지 제목은 주요 카테고리 이름(예: "어린이")으로 표시합니다.
    """
    # URL로부터 받은 category_id로 기준이 되는 Category 객체를 가져옵니다.
    clicked_category_object = get_object_or_404(Category, id=category_id)

    # 페이지 제목 및 필터링에 사용할 주요 카테고리 이름(키워드) 추출
    display_name_for_title = ""
    filter_keyword = ""
    
    # 이름 끝에 있을 수 있는 '>'나 양옆 공백 제거
    processed_name = clicked_category_object.name.strip().rstrip('>')
    name_parts = processed_name.split('>') # '>'를 기준으로 분리

    if name_parts: # 분리된 부분이 하나 이상 있는지 확인
        if len(name_parts) > 1:
            # "상위>하위" 또는 "상위>중위>하위" 등 ">"가 포함된 경우,
            # 네비게이션 바에 표시된 이름은 보통 두 번째 부분이므로 이를 사용합니다.
            # (get_navigation_categories 함수가 그렇게 생성한다고 가정)
            key_name_part = name_parts[1].strip()
        else: # ">"가 없는 단일 이름인 경우 (예: "어린이" 자체가 Category.name)
            key_name_part = name_parts[0].strip()
        
        if key_name_part: # 추출된 부분이 비어있지 않다면
            display_name_for_title = key_name_part
            filter_keyword = key_name_part
        else: # ">"로 끝나는 경우 등 예외적으로 key_name_part가 비게 되면 fallback
            display_name_for_title = processed_name # 원본 이름을 제목으로 사용
            filter_keyword = processed_name # 원본 이름을 필터 키워드로 사용 (정확한 매칭)
    else: # processed_name 자체가 비어있는 극단적인 경우
        display_name_for_title = "카테고리" # 기본 제목
        # filter_keyword는 비어있으므로 아래에서 모든 책이 나오거나, 특정 로직 필요

    if not filter_keyword:
        # 키워드가 없는 경우 (예: Category 이름이 비정상적이거나 비어있는 경우)
        # 이 경우 모든 책을 보여주거나, 에러 처리하거나, clicked_category_object에 해당하는 책만 보여줄 수 있습니다.
        # 여기서는 안전하게 clicked_category_object에 해당하는 책만 보여주도록 합니다.
        book_list_for_category = Book.objects.filter(category=clicked_category_object).order_by('-pub_date')
        if not display_name_for_title: # 만약 display_name_for_title도 설정 안됐다면
             display_name_for_title = clicked_category_object.name # 원본 카테고리 이름을 제목으로 사용
    else:
        # filter_keyword를 포함하는 모든 Category 객체를 찾습니다.
        relevant_categories = Category.objects.filter(name__icontains=filter_keyword)
        # 해당 카테고리들에 속하는 모든 책들을 가져옵니다.
        book_list_for_category = Book.objects.filter(category__in=relevant_categories).order_by('-pub_date').distinct()

    paginator = Paginator(book_list_for_category, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # 상단 고정 네비게이션 바를 위한 카테고리 목록 (헬퍼 함수 사용)
    navigation_categories = get_navigation_categories() # 이 함수는 views.py 내에 정의되어 있어야 합니다.

    context = {
        'current_category': clicked_category_object, # 페이지네이션 링크 등에 활용 (원본 Category 객체)
        'page_title': display_name_for_title,       # 화면 H1 태그에 표시될 간결한 페이지 제목 (예: "어린이")
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'global_categories': navigation_categories,   # 고정 네비게이션 바용
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
                nav_list.append({
                    'id': cat.id,
                    'name': second_level_name,
                })
            if len(nav_list) >= 6:
                break
    return nav_list

def books_by_group_view(request, group_name):
    def normalize(s):
        return s.strip().replace(" ", "").lower()

    group_name = group_name.replace("-", "/")  # 슬러그 되돌리기
    normalized_target = normalize(group_name)

    all_books = Book.objects.select_related('category').order_by('-pub_date')
    filtered_books = []

    for book in all_books:
        if book.category:
            second = extract_second_level(book.category.name)
            group = classify_category_group(second)
            normalized_group = normalize(group)

            if normalized_group == normalized_target:
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

