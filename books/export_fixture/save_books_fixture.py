# books/export_fixture/save_books_fixture.py

import json
from books.models import Book

def export_books_fixture(path="books/fixtures/books.json"):
    fixture = []

    for book in Book.objects.all():
        fixture.append({
            "model": "books.book",
            "pk": book.pk,
            "fields": {
                "title": book.title,
                "isbn13": book.isbn13,
                "description": book.description,
                "cover_image_url": book.cover_image_url,
                "pub_date": book.pub_date,
                "link": book.link,
                "author": book.author_id,
                "category": book.category_id,
                "created_at": book.created_at.isoformat(),
                "is_bestseller": book.is_bestseller,
                "publisher": book.publisher,
            }
        })

    with open(path, "w", encoding="utf-8") as f:
        json.dump(fixture, f, ensure_ascii=False, indent=2)

    print(f"✅ books fixture saved to {path}")
