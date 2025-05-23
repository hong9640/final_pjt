from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from .utils import get_restricted_recommendations
from books.models import Book
from django.db.models import Q
from django.http import JsonResponse
import json
from recommendations.models import AIRecommendation, AIRecommendationBook

def get_recommendation(request):
    if request.method == 'POST':
        keyword = request.POST.get('query')
        recommended_titles = get_restricted_recommendations(keyword)

        # Book 모델에서 추천된 제목과 일치하는 책만 필터링
        books = Book.objects.filter(title__in=recommended_titles)

        return render(request, 'recommendations/recommend_result.html', {
            'keyword': keyword,
            'books': books
        })

def show_result(request):
    keyword = request.GET.get('keyword', '')
    recommended_titles = get_restricted_recommendations(keyword)

    # 제목 완전 일치 필터링 (추천 결과에 정확히 해당하는 책만 추출)
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

        # 응답
        data = {
            "books": [
                {
                    "id": book.id,
                    "title": book.title,
                    "cover_image_url": book.cover_image_url,
                    "author": book.author.name if book.author else ""
                } for book in books
            ]
        }
        return JsonResponse(data)