from accounts.models import BookProfileCard
from libraries.models import Library

def user_context(request):
    card = None
    my_library_books = []

    if request.user.is_authenticated:
        card = getattr(request.user, 'reading_card', None)
        my_library_books = Library.objects.filter(user=request.user).select_related('book')

    return {
        'card': card,
        'my_library_books': my_library_books,
    }
