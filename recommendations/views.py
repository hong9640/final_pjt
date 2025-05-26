from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from .utils import get_restricted_recommendations
from books.models import Book
from django.db.models import Q
from django.http import JsonResponse
import json
from recommendations.models import AIRecommendation, AIRecommendationBook
from libraries.models import Library  # ✅ 추가
from .utils import get_restricted_recommendations
from django.contrib.auth.decorators import login_required
from recommendations.library_recommend_utils import get_recommendation_ids_based_on_library



def get_recommendation(request):
    if request.method == 'POST':
        keyword = request.POST.get('query')
        recommended_titles = get_restricted_recommendations(keyword)

        books = Book.objects.filter(title__in=recommended_titles)

        return render(request, 'recommendations/recommend_result.html', {
            'keyword': keyword,
            'books': books
        })

def show_result(request):
    keyword = request.GET.get('keyword', '')
    recommended_titles = get_restricted_recommendations(keyword)

    books = Book.objects.filter(title__in=recommended_titles)

    return render(request, 'recommendations/recommend_result.html', {
        'keyword': keyword,
        'books': books
    })

@csrf_exempt
def get_recommendation_ajax(request):
    if request.method == 'POST':
        body = json.loads(request.body)
        keyword = body.get('query')
        titles = get_restricted_recommendations(keyword)
        books = Book.objects.filter(title__in=titles)

        # ✅ 추천 결과 저장
        if request.user.is_authenticated:
            recommendation = AIRecommendation.objects.create(user=request.user, input_text=keyword)
            for book in books:
                AIRecommendationBook.objects.create(
                    recommendation=recommendation,
                    book=book,
                    explanation="AI 추천"
                )

        # ✅ 사용자의 서재에 있는 책 ID 리스트
        my_library_book_ids = set()
        if request.user.is_authenticated:
            my_library_book_ids = set(
                Library.objects.filter(user=request.user, book__in=books).values_list('book_id', flat=True)
            )

        # ✅ 응답
        data = {
            "books": [
                {
                    "id": book.id,
                    "title": book.title,
                    "cover_image_url": book.cover_image_url,
                    "author": book.author.name if book.author else "",
                    "in_library": book.id in my_library_book_ids
                } for book in books
            ]
        }
        return JsonResponse(data)
    
@login_required
def card_based_recommendation(request):
    card = getattr(request.user, 'reading_card', None)
    if not card:
        return JsonResponse({'error': '독서카드 없음'}, status=404)

    keyword_parts = []
    if card.favorite_genres:
        keyword_parts.extend(card.favorite_genres)
    if card.mood:
        keyword_parts.append(card.mood)
    if card.introduction:
        keyword_parts.append(card.introduction)

    keyword = ", ".join(keyword_parts)
    titles = get_restricted_recommendations(keyword)
    books = Book.objects.filter(title__in=titles)

    recommendation = AIRecommendation.objects.create(user=request.user, input_text=keyword)
    for book in books:
        AIRecommendationBook.objects.create(
            recommendation=recommendation,
            book=book,
            explanation="독서카드 기반 추천"
        )

    # ✅ 내 서재에 담긴 책 ID
    my_library_ids = set(
        Library.objects.filter(user=request.user, book__in=books).values_list('book_id', flat=True)
    )

    return JsonResponse({
        'books': [
            {
                'id': book.id,
                'title': book.title,
                'cover_image_url': book.cover_image_url,
                'in_library': book.id in my_library_ids  # ✅ 이 줄 추가
            } for book in books
        ]
    })

@login_required
def library_based_recommendation(request):
    books_in_library = Library.objects.filter(user=request.user).select_related('book')
    if not books_in_library.exists():
        return JsonResponse({'error': '서재가 비어있습니다.'}, status=404)

    # 서재에 담긴 책 객체들
    library_books = [entry.book for entry in books_in_library]

    # GPT 추천 호출 → Book.id 리스트
    recommended_ids = get_recommendation_ids_based_on_library(library_books)
    print("GPT 추천된 Book.id 목록:", recommended_ids)

    books = Book.objects.filter(id__in=recommended_ids)

    # AIRecommendation 저장
    recommendation = AIRecommendation.objects.create(user=request.user, input_text="[서재 기반 추천]")
    for book in books:
        AIRecommendationBook.objects.create(
            recommendation=recommendation,
            book=book,
            explanation="서재 기반 추천"
        )

    # 이미 서재에 있는 책인지 확인
    my_library_ids = set(b.id for b in library_books)

    return JsonResponse({
        'books': [
            {
                'id': book.id,
                'title': book.title,
                'cover_image_url': book.cover_image_url,
                'in_library': book.id in my_library_ids
            } for book in books
        ]
    })