from accounts.models import BookProfileCard
from libraries.models import Library

def user_context(request):
    card = getattr(request.user, 'reading_card', None) if request.user.is_authenticated else None
    library_count = Library.objects.filter(user=request.user).count() if request.user.is_authenticated else 0

    return {
        'card': card,
        'my_library_books': range(library_count),  # length만 쓰는 경우
    }
