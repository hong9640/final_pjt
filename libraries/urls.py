# libraries/urls.py

from django.urls import path
from . import views  # libraries 앱의 views.py를 임포트합니다.

app_name = 'libraries'  # URL 네임스페이스를 설정합니다.

urlpatterns = [
    # 예를 들어, /library/add/1/ 와 같은 URL로 책 ID(book_id)를 받습니다.
    path('add/<int:book_id>/', views.add_to_library, name='add_to_library'),
    path('remove/<int:book_id>/', views.remove_from_library, name='remove_from_library'),
]