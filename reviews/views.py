# reviews/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseBadRequest
from .models import Review, Comment, Like
from .forms import ReviewForm, CommentForm
from books.models import Book # books 앱의 Book 모델 import
from django.urls import reverse
from django.contrib.auth import get_user_model

@login_required
def add_review(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    # 이미 해당 책에 리뷰를 작성했는지 확인 (선택 사항)
    # if Review.objects.filter(book=book, user=request.user).exists():
    #     messages.warning(request, '이미 이 책에 대한 리뷰를 작성하셨습니다.')
    #     return redirect(book.get_absolute_url() + f'#review-write-form') # Book 모델에 get_absolute_url 정의 필요 또는 books:book_detail 사용

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.book = book
            review.user = request.user
            if book.category: # 리뷰 작성 시점의 책 카테고리 이름 저장
                review.book_category_at_review = book.category.name
            review.save()
            messages.success(request, '리뷰가 성공적으로 등록되었습니다.')
            return redirect(review.get_book_detail_url() + f'#review-{review.id}')
        else:
            # 폼 유효성 검사 실패 시 메시지 처리
            # (폼 에러를 book_detail 템플릿에서 직접 보여주는 것이 더 사용자 친화적일 수 있습니다)
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label if form.fields[field].label else field}: {error}")
            # book_detail 뷰로 폼과 함께 redirect 하거나, 여기서 book_detail context를 다시 만들어 렌더링해야 함
            # 여기서는 단순 리다이렉트. 오류 표시는 book_detail 뷰에서 request.POST를 확인하여 폼을 다시 생성하는 방식 등으로 개선 가능
            return redirect(book.get_absolute_url() + '#reviewSubmissionForm') # Book 모델에 get_absolute_url 정의 필요
    else: # GET 요청 시 (보통 book_detail 페이지에서 폼이 표시됨)
        form = ReviewForm() 
    
    # GET 요청이거나 폼 유효성 검사 실패 시, 리뷰 작성 폼이 있는 책 상세 페이지로 이동
    # 이 로직은 보통 book_detail 뷰에서 처리하므로, add_review는 POST만 담당하는 것이 더 일반적입니다.
    # 만약 add_review에서 GET 요청으로 폼을 보여줘야 한다면, book_detail과 유사한 context가 필요합니다.
    # 여기서는 add_review URL로 직접 접근하는 경우는 없다고 가정하고, 
    # 실패 시 book_detail로 돌아가도록 합니다.
    return redirect(book.get_absolute_url())


@login_required
def edit_review(request, review_id):
    review_instance = get_object_or_404(Review, id=review_id)
    book_instance = review_instance.book

    if request.user != review_instance.user:
        messages.error(request, '이 리뷰를 수정할 권한이 없습니다.')
        return HttpResponseForbidden("이 리뷰를 수정할 권한이 없습니다.")

    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review_instance)
        if form.is_valid():
            updated_review = form.save(commit=False)
            # 리뷰 작성 시점의 카테고리는 수정 시 변경하지 않도록 합니다.
            # 만약 책의 현재 카테고리로 업데이트하려면 아래 주석 해제
            # if book_instance.category:
            #     updated_review.book_category_at_review = book_instance.category.name
            # else:
            #     updated_review.book_category_at_review = None
            updated_review.save()
            messages.success(request, '리뷰가 성공적으로 수정되었습니다.')
            return redirect(review_instance.get_book_detail_url() + f'#review-{review_instance.id}')
        else:
            # 폼 유효성 검사 실패 시 메시지
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label if form.fields[field].label else field}: {error}")
            # 실패 시에도 폼과 함께 수정 페이지를 다시 보여줌
    else: # GET 요청
        form = ReviewForm(instance=review_instance)

    context = {
        'form': form,
        'review': review_instance,
        'book': book_instance,
    }
    return render(request, 'reviews/edit_review_form.html', context)


@login_required
def delete_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    if request.user != review.user:
        messages.error(request, '리뷰를 삭제할 권한이 없습니다.')
        return HttpResponseForbidden("You are not allowed to delete this review.")
    
    book_detail_url_redirect = review.get_book_detail_url() # 삭제 후 돌아갈 URL
    if request.method == 'POST':
        review.delete()
        messages.success(request, '리뷰가 삭제되었습니다.')
        return redirect(book_detail_url_redirect)
    
    # GET 요청으로 삭제 확인 페이지를 보여주려면 별도 템플릿 필요
    # 여기서는 POST만 처리하고, GET 요청은 그냥 상세 페이지로 리다이렉트 (또는 에러)
    messages.warning(request, '잘못된 접근입니다. 삭제는 POST 요청으로 이루어져야 합니다.')
    return redirect(book_detail_url_redirect)


@login_required
def like_review(request, review_id):
    if not request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.method != 'POST':
        return HttpResponseBadRequest("잘못된 요청입니다.")

    review = get_object_or_404(Review, id=review_id)
    like, created = Like.objects.get_or_create(user=request.user, review=review)

    if not created:
        like.delete()
        liked = False
    else:
        liked = True
    
    like_count = review.likes_received.count()
    return JsonResponse({'liked': liked, 'like_count': like_count})


@login_required
def add_comment(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    redirect_url_with_anchor = review.get_book_detail_url() + f'#review-{review.id}'

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.review = review
            comment.user = request.user
            comment.save()
            messages.success(request, '댓글이 등록되었습니다.')
            return redirect(redirect_url_with_anchor)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"댓글 작성 실패: {form.fields[field].label if form.fields[field].label else field}: {error}")
            return redirect(redirect_url_with_anchor) # 에러가 있어도 같은 위치로
    return redirect(redirect_url_with_anchor) # GET 요청 시


@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    review = comment.review
    book_id = review.book.id
    redirect_url_with_anchor = review.get_book_detail_url() + f'#review-{review.id}'

    if request.user != comment.user:
        messages.error(request, '댓글을 삭제할 권한이 없습니다.')
        return HttpResponseForbidden("You are not allowed to delete this comment.")

    if request.method == 'POST':
        comment.delete()
        messages.success(request, '댓글이 삭제되었습니다.')
        return redirect(redirect_url_with_anchor)
    
    messages.warning(request, '잘못된 접근입니다.')
    return redirect(redirect_url_with_anchor)
    

def user_written_reviews(request, username):
    User = get_user_model()
    user_obj = get_object_or_404(User, username=username) # 변수명 변경 user -> user_obj
    reviews = Review.objects.filter(user=user_obj).select_related('book', 'user') # user 대신 user_obj
    # 페이지네이션 로직 추가 가능
    context = {
        'target_user': user_obj,
        'reviews': reviews,
        'global_categories': Book._meta.get_field('category').remote_field.model.objects.none(), # 임시, views.py 최상단 get_navigation_categories 사용 권장
        'category_groups': [], # 임시
    }
    # from books.views import get_navigation_categories, CATEGORY_GROUPS # 순환참조 주의
    # context['global_categories'] = get_navigation_categories()
    # context['category_groups'] = CATEGORY_GROUPS
    return render(request, 'reviews/user_written_reviews.html', context)

def user_liked_reviews(request, username):
    User = get_user_model()
    user_obj = get_object_or_404(User, username=username) # 변수명 변경 user -> user_obj
    likes = Like.objects.filter(user=user_obj).select_related('review__book', 'review__user') # user 대신 user_obj
    # 페이지네이션 로직 추가 가능
    context = {
        'target_user': user_obj,
        'likes': likes,
        'global_categories': Book._meta.get_field('category').remote_field.model.objects.none(), # 임시
        'category_groups': [], # 임시
    }
    return render(request, 'reviews/user_liked_reviews.html', context)

@login_required
def edit_comment(request, comment_id):
    comment_instance = get_object_or_404(Comment, id=comment_id)
    review = comment_instance.review # 해당 댓글이 달린 리뷰 객체
    book_instance = review.book # 해당 리뷰가 달린 책 객체

    if request.user != comment_instance.user:
        messages.error(request, '이 댓글을 수정할 권한이 없습니다.')
        return HttpResponseForbidden("이 댓글을 수정할 권한이 없습니다.")

    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment_instance)
        if form.is_valid():
            form.save()
            messages.success(request, '댓글이 성공적으로 수정되었습니다.')
            # 수정 후 해당 책 상세 페이지의 리뷰 위치로 리다이렉트
            return redirect(review.get_book_detail_url() + f'#comment-{comment_instance.id}') # Review 모델에 get_book_detail_url() 필요
    else:
        form = CommentForm(instance=comment_instance)

    context = {
        'form': form,
        'comment': comment_instance,
        'review': review, # 상위 리뷰 정보
        'book': book_instance, # 책 정보
    }
    return render(request, 'reviews/edit_comment_form.html', context)