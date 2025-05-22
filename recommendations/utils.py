# recommendations/utils.py
import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")  # 환경 변수로 API 키 불러오기

def get_book_recommendations(keyword):
    prompt = f"""
    '{keyword}' 키워드를 좋아하는 사람에게 추천할 만한 책 3권을 추천해줘.
    다음 형식으로만 출력해줘:

    책 제목 | 간단한 설명

    예시:
    해리 포터와 마법사의 돌 | 마법과 우정의 세계를 그린 성장 판타지
    어린 왕자 | 순수한 시선으로 인생을 성찰하는 철학 동화
    ...
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "당신은 책 추천 전문가입니다."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.8,
        )

        result_text = response['choices'][0]['message']['content']
        lines = result_text.strip().split('\n')
        
        books = []
        for line in lines:
            if "|" in line:
                title, desc = line.split("|", 1)
                books.append({
                    "title": title.strip(),
                    "desc": desc.strip()
                })

        return books

    except Exception as e:
        print("OpenAI Error:", e)
        return []
