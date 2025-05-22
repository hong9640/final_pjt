from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from .utils import get_restricted_recommendations
from books.models import Book

def get_recommendation(request):
    if request.method == 'POST':
        keyword = request.POST.get('query')
        books = get_restricted_recommendations(keyword)

        return render(request, 'recommendations/recommend_result.html', {
            'keyword': keyword,
            'books': books
        })

def show_result(request):
    keyword = request.GET.get('keyword', '')
    recommended_titles = get_restricted_recommendations(keyword)

    # contains 방식으로 필터링 (제목 일부라도 포함되면 OK)
    from django.db.models import Q
    query = Q()
    for title in recommended_titles:
        query |= Q(title__icontains=title)

    books = Book.objects.filter(query)

    return render(request, 'recommendations/recommend_result.html', {
        'keyword': keyword,
        'books': books
    })
