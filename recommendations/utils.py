# utils.py
import openai
import os
from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_restricted_recommendations(keyword):
    from books.models import Book

    all_books = Book.objects.all()

    book_list_text = ""
    for book in all_books:
        title = book.title.strip().replace("\n", " ")
        desc = (book.description or "설명 없음").strip().replace("\n", " ")
        book_list_text += f"- {title}: {desc[:80]}...\n"

    prompt = f"""
아래는 추천 가능한 책 목록이야. 이 목록 안에서 '{keyword}' 키워드를 좋아하는 사람에게 어울릴 만한 책 3권을 추천해줘.

**절대 목록에 없는 책을 만들어내지 마. 반드시 아래에 나열된 책 제목 중에서만 골라줘.**

**책 설명 없이, 책 제목만 줄 단위로 정확하게 출력해줘.**

**다른 말이나 인사, 감상은 절대 포함하지 마.**

출력 예시:
우정 자판기  
노년에 관하여 우정에 관하여  
우정 도둑

책 목록:
{book_list_text}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 도서 큐레이터입니다."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7,
        )

        content = response.choices[0].message.content
        lines = content.strip().split("\n")
        recommended_titles = [line.strip() for line in lines if line.strip()]
        return recommended_titles

    except Exception as e:
        print("OpenAI Error:", e)
        return []
