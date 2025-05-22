# books/export_fixture/save_categories_fixture.py

import json
from books.models import Category

def export_categories_fixture(path="books/fixtures/categories.json"):
    fixture = []

    for category in Category.objects.all():
        fixture.append({
            "model": "books.category",
            "pk": category.pk,
            "fields": {
                "name": category.name,
                "created_at": category.created_at.isoformat(),
            }
        })

    with open(path, "w", encoding="utf-8") as f:
        json.dump(fixture, f, ensure_ascii=False, indent=2)

    print(f"✅ categories fixture saved to {path}")
