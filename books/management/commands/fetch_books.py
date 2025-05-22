# books/management/commands/fetch_books.py

import os
import requests
from dotenv import load_dotenv

from django.core.management.base import BaseCommand
from books.models import Book, Author, Category

load_dotenv()  # .env 파일 로드

class Command(BaseCommand):
    help = 'Fetch books from Aladin API and save to DB'

    def handle(self, *args, **options):
        ttb_key = os.getenv("ALADIN_TTBKEY")
        if not ttb_key:
            self.stderr.write("API 키가 설정되어 있지 않습니다. .env에 ALADIN_TTBKEY를 확인하세요.")
            return

        url = "https://www.aladin.co.kr/ttb/api/ItemSearch.aspx"
        params = {
            "ttbkey": ttb_key,
            "Query": "우정",  # 추천 키워드
            "QueryType": "Keyword",
            "MaxResults": 100,
            "start": 1,
            "SearchTarget": "Book",
            "output": "js",
            "Version": "20131101",
            "Cover": "Big"
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
        except requests.RequestException as e:
            self.stderr.write(f"API 요청 실패: {e}")
            return

        data = response.json().get('item', [])
        self.stdout.write(f"불러온 책 수: {len(data)}")

        for item in data:
            author_name = item.get('author', '').strip()
            category_name = item.get('categoryName', '').strip()
            isbn13 = item.get('isbn13')

            if not isbn13 or not author_name or not item.get('title'):
                continue  # 필수값 없는 도서 건너뜀

            author, _ = Author.objects.get_or_create(name=author_name)
            category, _ = Category.objects.get_or_create(name=category_name)

            Book.objects.update_or_create(
                isbn13=isbn13,
                defaults={
                    "title": item['title'],
                    "author": author,
                    "category": category,
                    "description": item.get('description', ''),
                    "cover_image_url": item.get('cover', ''),
                    "pub_date": item.get('pubDate', ''),
                    "link": item.get('link', ''),
                }
            )
