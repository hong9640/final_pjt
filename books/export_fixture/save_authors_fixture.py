# books/export_fixture/save_authors_fixture.py

import json
from books.models import Author

def export_authors_fixture(path="books/fixtures/authors.json"):
    fixture = []

    for author in Author.objects.all():
        fixture.append({
            "model": "books.author",
            "pk": author.pk,
            "fields": {
                "name": author.name,
                "profile_image": author.profile_image,
                "biography": author.biography,
            }
        })

    with open(path, "w", encoding="utf-8") as f:
        json.dump(fixture, f, ensure_ascii=False, indent=2)

    print(f"✅ authors fixture saved to {path}")
