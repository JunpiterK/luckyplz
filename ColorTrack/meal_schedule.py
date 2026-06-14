import os
import matplotlib.pyplot as plt
import pandas as pd
from pandas.plotting import table

# 한글 폰트 설정 (간단하게)
plt.rcParams['font.family'] = 'Malgun Gothic'  # Windows 기본 한글 폰트
plt.rcParams['axes.unicode_minus'] = False

# 30일 식단 데이터
data = [
    ["1일", "소고기무국, 계란말이, 현미밥, 사과", "소불고기, 상추쌈, 오이무침, 멸치볶음"],
    ["2일", "불고기 김밥, 유부장국, 바나나", "된장찌개, 호박전, 나물반찬, 두부구이"],
    ["3일", "호박죽, 삶은 계란, 배추김치, 견과류", "닭볶음탕, 감자조림, 브로콜리 찜"],
    ["4일", "닭가슴살 샐러드, 토스트, 우유", "닭가슴살 크림파스타, 토마토 샐러드"],
    ["5일", "닭고기 야채죽, 김구이, 요구르트", "두부김치, 고등어구이, 시금치나물"],
    ["6일", "고등어조림, 콩나물국, 귤", "야채비빔밥, 계란후라이, 호두"],
    ["7일", "야채볶음밥, 달걀국, 오렌지", "돼지고기 김치찌개, 애호박볶음"],
    ["8일", "돼지고기 샌드위치, 견과류, 우유", "돼지고기 두루치기, 쌈채소"],
    ["9일", "김치볶음밥, 달걀말이, 바나나", "감자탕, 깻잎전"],
    ["10일", "감자전, 오이냉국, 현미밥, 사과", "오징어볶음, 미역국, 시금치무침"],
    ["11일", "오징어 주먹밥, 된장국, 견과류", "소고기 야채볶음, 양배추쌈"],
    ["12일", "소고기 장조림, 나물밥, 바나나", "연어구이, 아스파라거스 볶음"],
    ["13일", "연어샌드위치, 샐러드, 우유", "돼지갈비찜, 청경채볶음"],
    ["14일", "갈비탕, 깍두기, 오렌지", "갈비김치볶음밥, 콩나물국"],
    ["15일", "콩나물비빔밥, 김치전, 견과류", "닭갈비, 양파장아찌"],
    ["16일", "닭죽, 메추리알조림, 바나나", "새우볶음밥, 오이소박이"],
    ["17일", "새우계란찜, 김자반 주먹밥, 우유", "돼지 제육볶음, 쌈채소"],
    ["18일", "돼지불고기 김밥, 우동국물, 귤", "순두부찌개, 가지볶음"],
    ["19일", "가지전, 된장국, 현미밥, 견과류", "고등어구이, 부추겉절이"],
    ["20일", "고등어 김치찜, 달걀말이, 사과", "버섯불고기, 양배추쌈"],
    ["21일", "소고기 미역국, 계란볶음밥, 바나나", "닭볶음탕, 감자채볶음"],
    ["22일", "닭가슴살 샐러드, 토스트, 우유", "닭가슴살 카레라이스, 토마토"],
    ["23일", "야채카레 오믈렛, 오렌지", "두부버섯전골, 시금치 나물"],
    ["24일", "두부부침, 시금치된장국, 견과류", "오삼불고기, 상추쌈"],
    ["25일", "삼겹살김밥, 콩나물국, 바나나", "소고기 버섯볶음, 오이무침"],
    ["26일", "소고기야채죽, 김자반, 사과", "갈치조림, 호박볶음"],
    ["27일", "갈치구이, 김치콩나물국, 귤", "닭곰탕, 애호박전"],
    ["28일", "닭곰탕 칼국수, 견과류", "돼지김치찜, 가지나물"],
    ["29일", "돼지고기 야채죽, 오이김치, 바나나", "연어초밥, 된장국, 오이무침"],
    ["30일", "연어샐러드, 바게트빵, 우유", "김치찌개, 계란말이, 두부조림"]
]

# DataFrame 생성
df = pd.DataFrame(data, columns=["날짜", "아침 메뉴", "저녁 메뉴"])

# 저장 경로 설정
folder_path = r"C:\Non_documents\mealplan"
file_path = os.path.join(folder_path, "June_Meal_Plan.png")

print("=== 식단표 생성 시작 ===")
print(f"저장 경로: {file_path}")

# 폴더 생성
try:
    os.makedirs(folder_path, exist_ok=True)
    print(f"✅ 폴더 생성 완료: {folder_path}")
except Exception as e:
    print(f"❌ 폴더 생성 실패: {e}")
    exit()

# 그래프 생성
fig, ax = plt.subplots(figsize=(12, 20))
ax.axis('off')

# 테이블 생성 (인덱스 제거)
tbl = table(ax, df, loc='center', cellLoc='left', colWidths=[0.15, 0.425, 0.425])
tbl.auto_set_font_size(False)
tbl.set_fontsize(9)
tbl.scale(1.0, 1.5)

# 헤더 스타일링
for i in range(len(df.columns)):
    tbl[(0, i)].set_facecolor('#E8F4FD')
    tbl[(0, i)].set_text_props(weight='bold')

# 교대로 행 색깔 적용 (헤더 제외하고 데이터 행만)
for i in range(1, len(df) + 1):
    if i % 2 == 1:  # 홀수 행에 색깔 적용
        for j in range(len(df.columns)):
            tbl[(i, j)].set_facecolor('#F9F9F9')

# 제목
plt.title("🍽️ 6월 아침/저녁 영양균형 식단표 🥗", fontsize=16, fontweight='bold', pad=20)

# 저장
try:
    plt.savefig(file_path, bbox_inches='tight', dpi=200, facecolor='white')
    plt.close()
    
    # 파일 확인
    if os.path.exists(file_path):
        size = os.path.getsize(file_path)
        print(f"✅ 파일 생성 성공!")
        print(f"📁 경로: {file_path}")
        print(f"📊 크기: {size:,} bytes")
    else:
        print("❌ 파일이 생성되지 않았습니다.")
        
except Exception as e:
    print(f"❌ 저장 실패: {e}")
    import traceback
    traceback.print_exc()

print("=== 완료 ===")