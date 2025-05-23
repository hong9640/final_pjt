from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseBadRequest
from .models import Review, Comment, Like
from .forms import ReviewForm, CommentForm
from books.models import Book
from django.urls import reverse
from django.contrib.auth import get_user_model

@login_required
def add_review(request, book_id):
    """
    Handles adding a new review for a specific book.
    Requires user to be logged in.
    """
    book = get_object_or_404(Book, id=book_id)
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            # Prevent duplicate reviews by the same user for the same book (optional)
            # if Review.objects.filter(book=book, user=request.user).exists():
            #     messages.error(request, '이미 이 책에 대한 리뷰를 작성하셨습니다.')
            # else:
            review = form.save(commit=False)
            review.book = book
            review.user = request.user
            if book.category:
                review.book_category_at_review = book.category.name
            review.save()
            messages.success(request, '리뷰가 성공적으로 등록되었습니다.')
            return redirect('books:book_detail', book_id=book.id)
        else:
            # Collect error messages to display
            error_message_list = []
            for field, errors in form.errors.items():
                # Use field label if available, otherwise use field name
                field_label = form.fields.get(field).label if form.fields.get(field) and form.fields.get(field).label else field
                error_message_list.append(f"{field_label}: {', '.join(errors)}")
            messages.error(request, f"리뷰 작성에 실패했습니다: {'; '.join(error_message_list)}")
            # It's better to re-render the page with the form and errors,
            # but for simplicity, we redirect. To show errors, you'd pass the form
            # back to the book_detail context or handle review form submission on book_detail itself.
            return redirect('books:book_detail', book_id=book.id) # Consider how to show errors on redirect
    else:
        # If not POST, redirect to book detail (form is usually on book_detail page)
        return redirect('books:book_detail', book_id=book.id)

@login_required
def delete_review(request, review_id):
    """
    Handles deleting a review.
    Requires user to be logged in and be the author of the review.
    """
    review = get_object_or_404(Review, id=review_id)
    if request.user != review.user:
        messages.error(request, '리뷰를 삭제할 권한이 없습니다.')
        return HttpResponseForbidden("You are not allowed to delete this review.")
    
    if request.method == 'POST':
        book_id = review.book.id
        review.delete()
        messages.success(request, '리뷰가 삭제되었습니다.')
        return redirect('books:book_detail', book_id=book_id)
    else:
        # If GET request, perhaps show a confirmation page or simply redirect
        return redirect('books:book_detail', book_id=review.book.id)


@login_required
def like_review(request, review_id):
    """
    Handles liking or unliking a review.
    Requires user to be logged in. Returns JSON for AJAX requests.
    """
    if not request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.method != 'POST':
        return HttpResponseBadRequest("잘못된 요청입니다. AJAX POST 요청이어야 합니다.")

    review = get_object_or_404(Review, id=review_id)
    like, created = Like.objects.get_or_create(user=request.user, review=review)

    if not created: # If like already existed, it means user is unliking
        like.delete()
        liked = False
    else: # If like was created, user is liking
        liked = True
    
    like_count = review.likes_received.count()
    return JsonResponse({'liked': liked, 'like_count': like_count})


@login_required
def add_comment(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.review = review
            comment.user = request.user
            comment.save()
            messages.success(request, '댓글이 등록되었습니다.')
            
            # 방법 2: reverse를 사용하여 리다이렉트 URL 생성
            # 'books:book_detail'은 books 앱의 urls.py에 정의된 URL 이름이어야 합니다.
            # kwargs로 URL 패턴에 필요한 인자를 전달합니다.
            redirect_url = reverse('books:book_detail', kwargs={'book_id': review.book.id})
            return redirect(f"{redirect_url}#review-{review.id}")
        else:
            error_message_list = []
            for field, errors in form.errors.items():
                field_label = form.fields.get(field).label if form.fields.get(field) and form.fields.get(field).label else field
                error_message_list.append(f"{field_label}: {', '.join(errors)}")
            messages.error(request, f"댓글 작성에 실패했습니다: {'; '.join(error_message_list)}")
            
            # 오류 발생 시에도 동일한 방식으로 리다이렉트
            redirect_url = reverse('books:book_detail', kwargs={'book_id': review.book.id})
            return redirect(f"{redirect_url}#review-{review.id}") # 또는 오류 메시지를 포함하여 렌더링
    else:
        # GET 요청 시 책 상세 페이지로 리다이렉트
        return redirect('books:book_detail', book_id=review.book.id)


@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if request.user != comment.user:
        messages.error(request, '댓글을 삭제할 권한이 없습니다.')
        return HttpResponseForbidden("You are not allowed to delete this comment.")

    if request.method == 'POST':
        review = comment.review # 삭제 전에 review 객체를 가져옵니다.
        book_id = review.book.id # 리다이렉트를 위해 book_id를 저장합니다.
        comment.delete()
        messages.success(request, '댓글이 삭제되었습니다.')
        
        # 방법 2: reverse를 사용하여 리다이렉트 URL 생성
        redirect_url = reverse('books:book_detail', kwargs={'book_id': book_id})
        return redirect(f"{redirect_url}#review-{review.id}")
    else:
        # GET 요청 시 책 상세 페이지로 리다이렉트
        return redirect('books:book_detail', book_id=comment.review.book.id)
    

def user_written_reviews(request, username):
    User = get_user_model()
    user = get_object_or_404(User, username=username)
    reviews = Review.objects.filter(user=user).select_related('book')
    return render(request, 'reviews/user_written_reviews.html', {
        'target_user': user,
        'reviews': reviews,
    })

def user_liked_reviews(request, username):
    User = get_user_model()
    user = get_object_or_404(User, username=username)
    likes = Like.objects.filter(user=user).select_related('review__book', 'review__user')
    return render(request, 'reviews/user_liked_reviews.html', {
        'target_user': user,
        'likes': likes,
    })

