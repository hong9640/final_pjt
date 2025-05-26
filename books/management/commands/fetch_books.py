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

        keywords = [
            '사랑', '우정', '성장', '철학', '감동', '추리', '자기계발', '인문', '에세이', '여행',
            '청춘', '가족', '역사', '환경', '전쟁', '인생', '삶', '죽음', '고전', '과학',
            'SF', '판타지', '예술', '시', '수필', '문화', '교육', '심리', '직장', '리더십',
            '비즈니스', '창업', '기술', 'AI', '빅데이터', '연애', '중년', '미래', '사회', '정치'
        ]
        random.shuffle(keywords)

        collected_isbns = set()
        total_saved = 0
        max_books = 500

        total_saved = self.fetch_bestsellers(ttb_key, collected_isbns, total_saved, max_books)

        for keyword in keywords:
            if total_saved >= max_books:
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
                if total_saved >= max_books:
                    break
                total_saved = self.save_book_from_item(item, collected_isbns, total_saved)

        print(f"\n📦 총 저장 완료: {total_saved}권")

    def fetch_bestsellers(self, ttb_key, collected_isbns, total_saved, max_books):
        print("\n🔥 [베스트셀러 수집 시작]")
        url = "https://www.aladin.co.kr/ttb/api/ItemList.aspx"
        params = {
            "ttbkey": ttb_key,
            "QueryType": "Bestseller",
            "MaxResults": 50,
            "start": 1,
            "SearchTarget": "Book",
            "output": "js",
            "Version": "20131101",
            "Cover": "Big"
        }

        try:
            response = requests.get(url, params=params)
            if response.status_code != 200:
                print(f"❌ 베스트셀러 API 오류:\n{response.text}")
                return total_saved

            data = response.json().get('item', [])
            print(f"📚 베스트셀러 {len(data)}권 수신")

            for item in data:
                if total_saved >= max_books:
                    break
                total_saved = self.save_book_from_item(item, collected_isbns, total_saved)

        except Exception as e:
            print(f"🔻 베스트셀러 요청 실패: {e}")

        return total_saved

    def save_book_from_item(self, item, collected_isbns, total_saved):
        isbn13 = item.get('isbn13')
        if not isbn13 or isbn13 in collected_isbns:
            return total_saved

        title = item.get('title', '').strip()
        raw_author_name = item.get('author', '').strip()
        category_name = item.get('categoryName', '').strip()

        if not title or not raw_author_name:
            return total_saved

        print(f"✅ 저장 대상: {title[:30]} / {raw_author_name}")

        author, _ = Author.objects.get_or_create(name=raw_author_name)
        parsed_author_name = self.extract_primary_author_name(raw_author_name)
        wiki_data = self.get_wikipedia_data(parsed_author_name)

        if not wiki_data:
            print(f"🚫 작가 '{parsed_author_name}' 위키 정보 없음 → 저장 건너뜀")
            return total_saved

        author.profile_image = wiki_data.get('thumbnail', {}).get('source')
        author.biography = wiki_data.get('extract', '')
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
                "is_bestseller": bool(item.get('bestRank', 0)),
            }
        )

        collected_isbns.add(isbn13)
        return total_saved + 1

    def extract_primary_author_name(self, raw_author_str):
        parts = [part.strip() for part in raw_author_str.split(',')]
        first = parts[0]
        return re.sub(r'\([^)]*\)', '', first).strip()

    def get_wikipedia_data(self, author_name):
        try:
            titles = self.search_wikipedia_titles(author_name)
            best_title = self.filter_likely_author_title(titles)
            if not best_title:
                print(f"❌ '{author_name}'에 대한 적절한 문서 없음")
                return None

            summary_url = f"https://ko.wikipedia.org/api/rest_v1/page/summary/{best_title}"
            response = requests.get(summary_url)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"🔻 위키피디아 요청 실패: {author_name} / {e}")
        return None

    def search_wikipedia_titles(self, author_name):
        try:
            search_url = "https://ko.wikipedia.org/w/api.php"
            params = {
                "action": "opensearch",
                "search": author_name,
                "limit": 5,
                "namespace": 0,
                "format": "json"
            }
            response = requests.get(search_url, params=params)
            if response.status_code == 200:
                _, titles, *_ = response.json()
                print(f"🔍 '{author_name}' 검색 결과: {titles}")
                return titles
        except Exception as e:
            print(f"🔍 검색 실패: {e}")
        return []

    def filter_likely_author_title(self, titles):
        for title in titles:
            if any(keyword in title for keyword in ['작가', '소설가', '시인', '수필가']):
                return title
        return titles[0] if titles else None
