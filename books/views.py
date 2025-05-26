# books/views.py
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
from .models import Book, Category, Author
from libraries.models import Library
from reviews.models import Review, Like
from reviews.forms import ReviewForm, CommentForm
import re
from collections import defaultdict, OrderedDict
from django.db.models import Q, Avg

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
    search_type = request.GET.get('search_type', 'integrated')

    context = {
        'query': query,
        'search_type': search_type,
        'global_categories': get_navigation_categories(),
        'category_groups': CATEGORY_GROUPS, # 이 변수는 왼쪽 사이드바 네비게이션용으로 사용
    }

    if query:
        books_qs = Book.objects.all()

        if search_type == 'title':
            books_qs = books_qs.filter(title__icontains=query)
            context['page_title'] = f"'{query}' (제목) 검색 결과"
        elif search_type == 'author':
            books_qs = books_qs.filter(author__name__icontains=query)
            context['page_title'] = f"'{query}' (작가) 검색 결과"
        elif search_type == 'publisher':
            books_qs = books_qs.filter(publisher__icontains=query)
            context['page_title'] = f"'{query}' (출판사) 검색 결과"
        else: # 'integrated' 또는 기타
            books_qs = books_qs.filter(
                Q(title__icontains=query) |
                Q(author__name__icontains=query) |
                Q(publisher__icontains=query)
            ).distinct()
            context['page_title'] = f"'{query}' (통합) 검색 결과"

        searched_books_list = books_qs.order_by('-pub_date')
        paginator = Paginator(searched_books_list, 12)
        page_number_str = request.GET.get('page')
        page_obj = paginator.get_page(page_number_str)
        pagination_context_for_search = _get_custom_pagination_context(page_obj, paginator)

        context['page_obj'] = page_obj
        context['is_paginated'] = page_obj.has_other_pages()
        context.update(pagination_context_for_search)

    else:
        # --- 베스트셀러 순서 정렬을 위한 로직 수정 시작 ---
        bestseller_books_qs = Book.objects.filter(is_bestseller=True).select_related('category')
        
        # 1. 임시로 모든 베스트셀러를 그룹별로 분류 (기존 방식과 유사)
        temp_grouped_bestsellers = defaultdict(list)
        for book in bestseller_books_qs:
            if book.category:
                second_level = extract_second_level(book.category.name)
                group = classify_category_group(second_level)
            else:
                group = "기타"
            temp_grouped_bestsellers[group].append(book)

        # 2. CATEGORY_GROUPS (원하는 순서)를 기준으로 최종 데이터 생성
        ordered_grouped_bestsellers_for_template = OrderedDict()
        ordered_bestseller_groups_for_tabs = []

        for desired_group_name in CATEGORY_GROUPS: # 정의된 순서대로 반복
            if desired_group_name in temp_grouped_bestsellers and temp_grouped_bestsellers[desired_group_name]:
                # 해당 그룹에 책이 있는 경우에만 추가
                ordered_grouped_bestsellers_for_template[desired_group_name] = temp_grouped_bestsellers[desired_group_name]
                # 탭용 리스트에도 그룹 이름 추가 (중복 없이)
                if desired_group_name not in ordered_bestseller_groups_for_tabs:
                     ordered_bestseller_groups_for_tabs.append(desired_group_name)
        
        # (선택 사항) CATEGORY_GROUPS에 없지만 temp_grouped_bestsellers에는 있는 그룹 처리
        # 예를 들어, 분류 결과 새로운 그룹이 생겼고, 이를 맨 뒤에 추가하고 싶다면 아래 주석 해제 후 로직 추가
        # for group_name, books in temp_grouped_bestsellers.items():
        #     if group_name not in ordered_grouped_bestsellers_for_template and books: # 아직 추가 안됐고 책이 있다면
        #         ordered_grouped_bestsellers_for_template[group_name] = books
        #         if group_name not in ordered_bestseller_groups_for_tabs:
        #             ordered_bestseller_groups_for_tabs.append(group_name)

        # --- 베스트셀러 순서 정렬 로직 수정 끝 ---

        new_books_qs = Book.objects.order_by('-pub_date')[:8]
        all_latest_reviews_list = Review.objects.select_related('book', 'user').order_by('-created_at')
        review_paginator = Paginator(all_latest_reviews_list, 5)
        review_page_number = request.GET.get('review_page')
        latest_reviews_page_obj = review_paginator.get_page(review_page_number) # get_page 사용

        context.update({
            'grouped_bestsellers': ordered_grouped_bestsellers_for_template, # 정렬된 OrderedDict 전달
            'bestseller_groups': ordered_bestseller_groups_for_tabs,     # 정렬된 리스트 전달
            'new_books': new_books_qs,
            'latest_reviews_page': latest_reviews_page_obj,
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

    if author and isinstance(author.name, str):
        clean_author_name = re.sub(r'\s*\([^)]*\)', '', author.name.split(',')[0].strip())
    elif author:
        clean_author_name = str(author.name) if author.name else "정보 없음"
    else:
        clean_author_name = "정보 없음"

    is_in_library = False
    if request.user.is_authenticated:
        is_in_library = Library.objects.filter(user=request.user, book=book).exists()

    # 해당 책의 모든 리뷰를 가져옵니다. (기존 코드 활용)
    book_reviews_qs = book.reviews.select_related('user').prefetch_related(
        'comments__user',
        'likes_received'
    ).order_by('-created_at')

    # --- 평균 별점 계산 로직 추가 ---
    average_rating_data = book_reviews_qs.aggregate(avg_rating=Avg('rating')) # book_reviews_qs를 사용하거나 book.reviews.all() 사용
    average_rating = average_rating_data.get('avg_rating')
    reviews_count = book_reviews_qs.count() # 전체 리뷰 개수

    if average_rating is not None:
        average_rating = round(average_rating, 1) # 소수점 첫째 자리까지 반올림
    # else: # average_rating이 None일 경우 템플릿에서 처리하거나 여기서 기본값 설정 가능
        # average_rating = 0 # 예시: 리뷰가 없을 때 0으로 표시하고 싶다면

    # --- 평균 별점 계산 로직 끝 ---

    reviews_with_details = []
    liked_ids = set()
    if request.user.is_authenticated:
        liked_ids = set(
            Like.objects.filter(user=request.user, review__in=book_reviews_qs)
            .values_list('review_id', flat=True)
        )

    for review in book_reviews_qs:
        processed_category_for_review = "기타"
        if review.book_category_at_review:
            second_level_for_review = extract_second_level(review.book_category_at_review)
            processed_category_for_review = classify_category_group(second_level_for_review)
        
        reviews_with_details.append({
            'review_obj': review,
            'like_count': review.likes_received.count(),
            'user_has_liked': review.id in liked_ids,
            'comments_list': review.comments.all().order_by('created_at'),
            'display_category_group': processed_category_for_review,
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
        # --- 평균 별점 및 리뷰 개수를 context에 추가 ---
        'average_rating': average_rating,
        'reviews_count': reviews_count,
    }
    return render(request, 'books/book_detail.html', context)


def all_books_list(request):
    query = request.GET.get('q')
    search_type = request.GET.get('search_type', 'integrated') # 기본값 통합검색
    
    book_list_qs = Book.objects.all() # 기본 QuerySet: 모든 책
    page_title_display = "전체 도서"

    if query:
        if search_type == 'title':
            book_list_qs = book_list_qs.filter(title__icontains=query)
            page_title_display = f"'{query}' (제목) 검색 결과"
        elif search_type == 'author':
            book_list_qs = book_list_qs.filter(author__name__icontains=query)
            page_title_display = f"'{query}' (작가) 검색 결과"
        elif search_type == 'publisher':
            book_list_qs = book_list_qs.filter(publisher__icontains=query)
            page_title_display = f"'{query}' (출판사) 검색 결과"
        else: # 'integrated' 또는 기타
            book_list_qs = book_list_qs.filter(
                Q(title__icontains=query) |
                Q(author__name__icontains=query) |
                Q(publisher__icontains=query)
            ).distinct()
            page_title_display = f"'{query}' (통합) 검색 결과"
        page_title_display += " (전체 도서)" # 검색 시 범위 명시

    book_list_qs = book_list_qs.order_by('-pub_date')

    paginator = Paginator(book_list_qs, 12)
    page_number_str = request.GET.get('page')
    page_obj = paginator.get_page(page_number_str)
    pagination_context = _get_custom_pagination_context(page_obj, paginator)

    context = {
        'page_title': page_title_display,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        **pagination_context,
        'search_type': search_type, # 템플릿 전달
        'query': query,
        'global_categories': get_navigation_categories(),
        'category_groups': CATEGORY_GROUPS,
    }
    return render(request, 'books/category_total.html', context)

def books_by_category_view(request, category_id):
    query = request.GET.get('q')
    search_type = request.GET.get('search_type', 'integrated')
    clicked_category_object = get_object_or_404(Category, id=category_id)

    processed_name = clicked_category_object.name.strip().rstrip('>')
    name_parts = processed_name.split('>')
    key_name_part = name_parts[1].strip() if len(name_parts) > 1 else name_parts[0].strip()
    
    page_title_display = key_name_part # 기본 제목

    # 1. 해당 카테고리의 책 목록 QuerySet 가져오기
    relevant_categories = Category.objects.filter(name__icontains=key_name_part) # 기존 로직 유지
    book_list_qs = Book.objects.filter(category__in=relevant_categories).distinct()

    if query: # 검색어가 있을 경우, 위에서 필터링된 book_list_qs에 대해 추가 검색
        if search_type == 'title':
            book_list_qs = book_list_qs.filter(title__icontains=query)
            page_title_display = f"'{query}' (제목) 검색 결과 ({key_name_part})"
        elif search_type == 'author':
            book_list_qs = book_list_qs.filter(author__name__icontains=query)
            page_title_display = f"'{query}' (작가) 검색 결과 ({key_name_part})"
        elif search_type == 'publisher':
            book_list_qs = book_list_qs.filter(publisher__icontains=query)
            page_title_display = f"'{query}' (출판사) 검색 결과 ({key_name_part})"
        else: # 'integrated' 또는 기타
            book_list_qs = book_list_qs.filter(
                Q(title__icontains=query) |
                Q(author__name__icontains=query) |
                Q(publisher__icontains=query)
            ).distinct()
            page_title_display = f"'{query}' (통합) 검색 결과 ({key_name_part})"
            
    book_list_qs = book_list_qs.order_by('-pub_date')

    paginator = Paginator(book_list_qs, 12)
    page_number_str = request.GET.get('page')
    page_obj = paginator.get_page(page_number_str)
    pagination_context = _get_custom_pagination_context(page_obj, paginator)

    context = {
        'current_category_object': clicked_category_object,
        'page_title': page_title_display,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        **pagination_context,
        'search_type': search_type,
        'query': query,
        'global_categories': get_navigation_categories(),
        'category_groups': CATEGORY_GROUPS,
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
    query = request.GET.get('q')
    search_type = request.GET.get('search_type', 'integrated')
    
    actual_group_display_name = group_name 
    for cat_group_in_list in CATEGORY_GROUPS:
        if cat_group_in_list.replace("/", "-").lower() == group_name.lower():
            actual_group_display_name = cat_group_in_list
            break
    if group_name.lower() == "기타":
        actual_group_display_name = "기타"

    # --- 그룹에 해당하는 책 QuerySet 가져오기 (수정된 부분) ---
    book_list_qs = Book.objects.all() # 전체 책에서 시작
    group_map_for_filtering = { # classify_category_group 내부의 group_map
        "문학/소설": ["소설", "시", "희곡", "장르소설", "문학"],
        "어린이/청소년": ["어린이", "초등", "청소년"],
        "만화/웹툰": ["만화", "웹툰", "라이트노벨"],
        "인문/사회": ["인문", "철학", "역사", "사회", "종교", "정치", "심리"],
        "자기계발/경제": ["자기계발", "경제", "경영", "투자", "재테크", "비즈니스"],
        "건강/취미": ["건강", "취미", "요리", "여행", "스포츠", "반려동물"],
        "교육/수험서": ["수험서", "자격증", "교재", "외국어", "컴퓨터", "IT", "학습"],
    }

    if actual_group_display_name != "기타" and actual_group_display_name in group_map_for_filtering:
        keywords_for_group = group_map_for_filtering[actual_group_display_name]
        # Category의 name 필드에서 (국내도서> 이후 부분) 키워드를 포함하는 Category를 찾음
        category_q_filter = Q()
        for keyword in keywords_for_group:
            # 예: "국내도서>소설", "국내도서>청소년 소설" 등을 모두 잡기 위해
            # 보다 정교한 필터링이 필요할 수 있습니다. 여기서는 간단히 keyword 포함으로 처리.
            category_q_filter |= Q(category__name__icontains=keyword) 
        book_list_qs = book_list_qs.filter(category_q_filter).distinct()
    elif actual_group_display_name == "기타":
        pass # book_list_qs is Book.objects.all()
    else: # 매칭되는 그룹이 없는 경우
        book_list_qs = Book.objects.none() # 빈 결과
    # --- 그룹 필터링 끝 ---
            
    page_title_display = actual_group_display_name

    if query: # 검색어가 있을 경우, 위에서 필터링된 book_list_qs에 대해 추가 검색
        if search_type == 'title':
            book_list_qs = book_list_qs.filter(title__icontains=query)
            page_title_display = f"'{query}' (제목) 검색 결과 ({actual_group_display_name})"
        elif search_type == 'author':
            book_list_qs = book_list_qs.filter(author__name__icontains=query)
            page_title_display = f"'{query}' (작가) 검색 결과 ({actual_group_display_name})"
        elif search_type == 'publisher':
            book_list_qs = book_list_qs.filter(publisher__icontains=query)
            page_title_display = f"'{query}' (출판사) 검색 결과 ({actual_group_display_name})"
        else: # 'integrated' 또는 기타
            book_list_qs = book_list_qs.filter(
                Q(title__icontains=query) |
                Q(author__name__icontains=query) |
                Q(publisher__icontains=query)
            ).distinct()
            page_title_display = f"'{query}' (통합) 검색 결과 ({actual_group_display_name})"

    book_list_qs = book_list_qs.order_by('-pub_date')
    
    paginator = Paginator(book_list_qs, 12)
    page_number_str = request.GET.get('page')
    page_obj = paginator.get_page(page_number_str)
    pagination_context = _get_custom_pagination_context(page_obj, paginator)

    context = {
        'page_title': page_title_display,
        'current_group_slug': group_name,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        **pagination_context,
        'search_type': search_type,
        'query': query,
        'global_categories': get_navigation_categories(),
        'category_groups': CATEGORY_GROUPS,
    }
    return render(request, 'books/category.html', context)

def _get_custom_pagination_context(page_obj, paginator):
    """Helper function to create pagination context."""
    current_page_num = page_obj.number
    total_pages = paginator.num_pages
    pagination_block_size = 5

    if total_pages <= pagination_block_size:
        start_display = 1
        end_display = total_pages
    else:
        start_display = current_page_num - (pagination_block_size // 2)
        end_display = current_page_num + (pagination_block_size // 2)
        if start_display < 1:
            end_display = min(total_pages, end_display + (1 - start_display))
            start_display = 1
        if end_display > total_pages:
            start_display = max(1, start_display - (end_display - total_pages))
            end_display = total_pages
        if (end_display - start_display + 1) < pagination_block_size and total_pages >= pagination_block_size:
            if start_display == 1:
                end_display = min(start_display + pagination_block_size - 1, total_pages)
            elif end_display == total_pages:
                start_display = max(1, end_display - pagination_block_size + 1)
    visible_page_numbers = list(range(start_display, end_display + 1))
    prev_single_page_target = page_obj.previous_page_number() if page_obj.has_previous() else None
    next_single_page_target = page_obj.next_page_number() if page_obj.has_next() else None
    first_page_jump_target = 1 if current_page_num > 1 else None
    last_page_jump_target = total_pages if current_page_num < total_pages else None
    return {
        'visible_page_numbers': visible_page_numbers,
        'prev_single_page_target': prev_single_page_target,
        'next_single_page_target': next_single_page_target,
        'first_page_jump_target': first_page_jump_target,
        'last_page_jump_target': last_page_jump_target,
        'total_pages_for_template': total_pages,
    }