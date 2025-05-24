import os
import random
import requests
import re
from dotenv import load_dotenv
from django.core.management.base import BaseCommand
from books.models import Book, Author, Category

load_dotenv()

class Command(BaseCommand):
    help = '도서 수집 및 작가 정보를 위키피디아에서 가져옵니다 (정제된 이름 기준)'

    def handle(self, *args, **options):
        ttb_key = os.getenv("ALADIN_TTBKEY")
        if not ttb_key:
            print("❌ ALADIN_TTBKEY 환경변수가 없습니다.")
            return
        else:
            print(f"✅ ALADIN_TTBKEY 로드 성공: {ttb_key[:5]}******")

        keywords = ['사랑', '우정', '성장', '철학', '감동', '추리', '자기계발', '인문', '에세이', '여행']
        random.shuffle(keywords)

        collected_isbns = set()
        total_saved = 0

        for keyword in keywords:
            if total_saved >= 300:
                break

            print(f"\n🔍 키워드 '{keyword}'에서 책 수집 중...")

            search_url = "https://www.aladin.co.kr/ttb/api/ItemSearch.aspx"
            search_params = {
                "ttbkey": ttb_key,
                "Query": keyword,
                "QueryType": "Keyword",
                "MaxResults": 100,
                "start": 1,
                "SearchTarget": "Book",
                "output": "js",
                "Version": "20131101",
                "Cover": "Big"
            }

            try:
                response = requests.get(search_url, params=search_params)
                print(f"[응답 상태 코드] {response.status_code}")

                if response.status_code != 200:
                    print(f"⚠️ API 오류 응답:\n{response.text[:300]}...")
                    continue

                data = response.json().get('item', [])
                print(f"📚 '{keyword}' 키워드로 {len(data)}권 수신")

            except requests.RequestException as e:
                print(f"🔴 요청 예외 발생: {e}")
                continue

            for item in data:
                if total_saved >= 300:
                    break

                isbn13 = item.get('isbn13')
                if not isbn13:
                    print("❌ ISBN13 없음 → 건너뜀")
                    continue
                if isbn13 in collected_isbns:
                    print("🔁 중복 ISBN13 → 건너뜀")
                    continue

                title = item.get('title', '').strip()
                raw_author_name = item.get('author', '').strip()
                category_name = item.get('categoryName', '').strip()

                if not title or not raw_author_name:
                    print("❌ 제목 또는 저자 없음 → 건너뜀")
                    continue

                print(f"✅ 저장 대상: {title[:30]} / {raw_author_name} / 출판사: {item.get('publisher')}")

                author, _ = Author.objects.get_or_create(name=raw_author_name)

                parsed_author_name = self.extract_primary_author_name(raw_author_name)
                wiki_data = self.get_wikipedia_data(parsed_author_name)

                author.profile_image = wiki_data.get('thumbnail', {}).get('source') if wiki_data else None
                author.biography = wiki_data.get('extract') if wiki_data else ''
                author.save()

                category, _ = Category.objects.get_or_create(name=category_name)

                Book.objects.update_or_create(
                    isbn13=isbn13,
                    defaults={
                        "title": title,
                        "author": author,
                        "category": category,
                        "description": item.get('description', ''),
                        "cover_image_url": item.get('cover', ''),
                        "pub_date": item.get('pubDate', ''),
                        "publisher": item.get('publisher', ''),
                        "link": item.get('link', ''),
                    }
                )

                collected_isbns.add(isbn13)
                total_saved += 1

        print(f"\n📦 총 저장 완료: {total_saved}권")

    def extract_primary_author_name(self, raw_author_str):
        parts = [part.strip() for part in raw_author_str.split(',')]
        first = parts[0]
        return re.sub(r'\([^)]*\)', '', first).strip()

    def get_wikipedia_data(self, author_name):
        try:
            url = f"https://ko.wikipedia.org/api/rest_v1/page/summary/{author_name}"
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"🔻 위키피디아 요청 실패: {author_name} / {e}")
        return None
