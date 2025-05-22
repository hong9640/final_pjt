from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from .utils import get_book_recommendations

@csrf_exempt
def get_recommendation(request):
    if request.method == 'POST':
        query = request.POST.get('query')
        # 여기서 AI 추천 로직 실행 예정
        return render(request, 'recommendations/result.html', {'query': query})
    return render(request, 'recommendations/input.html')

def get_recommendation(request):
    if request.method == 'POST':
        keyword = request.POST.get('query')
        books = get_book_recommendations(keyword)

        return render(request, 'recommendations/recommend_result.html', {
            'keyword': keyword,
            'books': books
        })