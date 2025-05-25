# books/context_processors.py
from books.models import Category

CATEGORY_GROUPS = [
    "문학/소설", "어린이/청소년", "만화/웹툰",
    "인문/사회", "자기계발/경제", "건강/취미",
    "교육/수험서", "기타"
]

def classify_category_group(second_level):
    group_map = {
        "문학/소설": ["소설", "시", "희곡", "장르소설", "문학"],
        "어린이/청소년": ["어린이", "초등", "청소년"],
        "만화/웹툰": ["만화", "웹툰", "라이트노벨"],
        "인문/사회": ["인문", "철학", "역사", "사회", "종교", "정치", "심리"],
        "자기계발/경제": ["자기계발", "경제", "경영", "투자", "재테크", "비즈니스"],
        "건강/취미": ["건강", "취미", "요리", "여행", "스포츠", "반려동물"],
        "교육/수험서": ["수험서", "자격증", "교재", "외국어", "컴퓨터", "IT", "학습"],
    }
    for group, keywords in group_map.items():
        if any(keyword in second_level for keyword in keywords):
            return group
    return "기타"

def category_groups_processor(request):
    categories = Category.objects.filter(name__startswith="국내도서>")
    group_set = set()

    for cat in categories:
        parts = cat.name.split(">")
        if len(parts) > 1:
            second_level = parts[1].strip()
            group = classify_category_group(second_level)
            group_set.add(group)

    # 📌 CATEGORY_GROUPS 기준으로 정렬
    sorted_groups = [g for g in CATEGORY_GROUPS if g in group_set]
    return {
        'category_groups': ['전체'] + sorted_groups
    }
