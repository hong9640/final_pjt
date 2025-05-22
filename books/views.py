from django.http import JsonResponse

from django.shortcuts import render
from .models import Category, Book

def home(request):
    categories_qs = Category.objects.filter(name__startswith="국내도서>")
    
    second_levels = []
    seen = set()
    for cat in categories_qs:
        parts = cat.name.split(">")
        if len(parts) > 1:
            second = parts[1].strip()
            if second not in seen:
                seen.add(second)
                second_levels.append({'name': second, 'display_name': second, 'id': cat.id})
            if len(second_levels) >= 6:
                break

    bestseller_books = Book.objects.filter(is_bestseller=True).select_related('category')[:1]
    new_books = Book.objects.order_by('-pub_date')[:6]

    context = {
        'categories': second_levels,
        'bestseller_books': bestseller_books,
        'new_books': new_books,
    }
    return render(request, 'books/home.html', context)

def bestseller_api(request):
    category_id = request.GET.get("category_id")
    books = Book.objects.filter(category_id=category_id, is_bestseller=True)[:6]
    data = {
        "books": [
            {
                "title": book.title,
                "cover_image_url": book.cover_image_url,
            } for book in books
        ]
    }
    return JsonResponse(data)


# def book_detail(request, book_id):
#     book = get_object_or_404(Book, id=book_id)
#     author = book.author
#     context = {
#         'book': book,
#         'author': author
#     }
#     return render(request, 'books/book_detail.html', context)

# def books_category(request, category_id):
#     category = get_object_or_404(Category, id=category_id)
#     books = Book.objects.filter(category=category).order_by('-created_at')
#     paginator = Paginator(books, 6)
#     page_number = request.GET.get('page')
#     page_obj = paginator.get_page(page_number)
#     context = {
#         'category': category,
#         'page_obj': page_obj
#     }
#     return render(request, 'books/category.html', context)

# def author_detail(request, author_id):
#     author = get_object_or_404(Author, id=author_id)
#     books_by_author = Book.objects.filter(author=author)

#     context = {
#         'author': author,
#         'books': books_by_author
#     }
#     return render(request, 'books/author_detail.html', context)

