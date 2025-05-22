from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def get_recommendation(request):
    if request.method == 'POST':
        query = request.POST.get('query')
        # 여기서 AI 추천 로직 실행 예정
        return render(request, 'recommendations/result.html', {'query': query})
    return render(request, 'recommendations/input.html')
