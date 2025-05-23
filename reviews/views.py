# reviews/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Review
from .forms import ReviewForm
from books.models import Book # Book 모델 임포트

@login_required
def add_review(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            # if Review.objects.filter(book=book, user=request.user).exists():
            #     messages.error(request, '이미 이 책에 대한 리뷰를 작성하셨습니다.')
            # else:
            review = form.save(commit=False)
            review.book = book
            review.user = request.user
            
            # 책의 카테고리 정보를 가져와서 리뷰에 저장
            if book.category: # 책에 카테고리가 할당되어 있다면
                review.book_category_at_review = book.category.name # Category 모델의 name 필드 사용 가정
            # else: 책에 카테고리가 없다면 review.book_category_at_review는 null로 저장됨 (모델 필드가 null=True일 경우)
            
            review.save()
            messages.success(request, '리뷰가 성공적으로 등록되었습니다.')
            return redirect('books:book_detail', book_id=book.id)
        else:
            error_message_list = []
            for field, errors in form.errors.items():
                error_message_list.append(f"{form.fields.get(field).label if form.fields.get(field) else field}: {', '.join(errors)}")
            messages.error(request, f"리뷰 작성에 실패했습니다: {'; '.join(error_message_list)}")
            # 실패 시 폼 데이터와 오류를 세션 등을 통해 book_detail로 전달하여 보여주는 것이 좋음
            # 여기서는 book_detail 뷰가 항상 새 폼을 만들므로, 이전 입력값과 오류는 사라짐.
            # 이를 개선하려면 book_detail 뷰에서 POST를 직접 처리하거나, 세션/GET 파라미터로 폼데이터/오류 전달 필요.
            # 지금은 간단히 리다이렉트합니다.
            return redirect('books:book_detail', book_id=book.id)
    else:
        return redirect('books:book_detail', book_id=book.id)