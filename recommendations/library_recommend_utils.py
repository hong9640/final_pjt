import openai
import os
from openai import OpenAI
import re

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_recommendation_ids_based_on_library(library_books):
    from books.models import Book

    all_books = Book.objects.all()
    library_ids = {book.id for book in library_books}

    user_books_text = ""
    all_books_text = ""

    for book in library_books:
        user_books_text += f"- {book.title.strip()}\n"

    for book in all_books:
        if book.id in library_ids:
            continue
        desc = (book.description or "설명 없음").strip().replace("\n", " ")
        all_books_text += f"{book.id}: {book.title.strip()} - {desc[:80]}...\n"

    prompt = f"""
사용자의 서재에는 다음과 같은 책들이 담겨 있어:
{user_books_text}

이 사용자가 좋아할 만한 책 3권을 추천해줘.
**반드시 아래 목록 안에 있는 ID를 사용해서 추천해줘. ID가 없는 책은 절대 추천하지 마.**

**출력은 오직 숫자만 줄 단위로 출력하고, 다른 설명은 절대 하지 마.**

추천 가능한 책 목록:
{all_books_text}

출력 예시:
12  
101  
301
"""


    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 도서 큐레이터입니다."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.7,
        )
        raw = response.choices[0].message.content
        print("GPT 응답 원문:\n", raw)
        ids = [int(num) for num in re.findall(r"\b\d+\b", raw)]
        return ids

    except Exception as e:
        print("OpenAI Error:", e)
        return []
