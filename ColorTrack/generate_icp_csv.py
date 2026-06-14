import os
import pandas as pd
import numpy as np

# 출력 디렉토리 및 파일 경로
output_dir = r"C:\non_documents\ColorTrack"
output_file = os.path.join(output_dir, "ICP.csv")

# 디렉토리 생성 (존재하지 않을 경우)
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# 데이터셋 크기
n_samples = 500

# 각도 리스트
angles = [0, 15, 30, 45, 60]

# 0° 기준 색좌표 (6500K, CIE 1931)
base_x, base_y = 0.3127, 0.3290

# VACS에 따른 각도별 색좌표 이동량 (예시 값, 실제 데이터로 조정 가능)
x_shifts = {0: 0.0, 15: -0.005, 30: -0.010, 45: -0.015, 60: -0.020}
y_shifts = {0: 0.0, 15: -0.003, 30: -0.006, 45: -0.009, 60: -0.012}

# 가우시안 분포 표준편차
sigma = 0.005

# 데이터 생성
data = {}
np.random.seed(42)  # 재현 가능성을 위한 시드 설정

for angle in angles:
    # 각도별 평균 색좌표
    mean_x = base_x + x_shifts[angle]
    mean_y = base_y + y_shifts[angle]
    
    # 가우시안 분포로 x, y 좌표 생성
    x_values = np.random.normal(mean_x, sigma, n_samples)
    y_values = np.random.normal(mean_y, sigma, n_samples)
    
    # 색좌표 범위 클리핑 (CIE 1931 유효 범위)
    x_values = np.clip(x_values, 0.0, 0.8)
    y_values = np.clip(y_values, 0.0, 0.9)
    
    # 데이터 딕셔너리에 추가
    data[f"{angle}_x"] = x_values
    data[f"{angle}_y"] = y_values

# pandas DataFrame 생성
df = pd.DataFrame(data)

# CSV 파일로 저장
df.to_csv(output_file, index=False)
print(f"CSV file saved to: {output_file}")

# 생성된 데이터의 첫 몇 줄 출력 (확인용)
print("\nFirst 5 rows of the generated dataset:")
print(df.head())