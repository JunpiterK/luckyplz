import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
from matplotlib.path import Path

# 출력 디렉토리
output_dir = r"C:\non_documents\ColorTrack"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# CIE 1931 2도 표준 관찰자 색 매칭 함수 (검증된 표준 데이터)
# Wyszecki & Stiles "Color Science" 기준의 정확한 데이터
def get_standard_cie1931_data():
    """표준 CIE 1931 색 매칭 함수 데이터 (5nm 간격)"""
    # 380nm부터 780nm까지 5nm 간격 (81개 점)
    wavelengths = np.arange(380, 785, 5)
    
    # CIE 1931 2° 표준 관찰자 XYZ 색 매칭 함수 (정확한 표준 값)
    x_bar = np.array([
        0.001368, 0.002236, 0.004243, 0.007650, 0.014310, 0.023190, 0.043510, 0.077630,
        0.134380, 0.214770, 0.283900, 0.328500, 0.348280, 0.348060, 0.336200, 0.318700,
        0.290800, 0.251100, 0.195360, 0.142100, 0.095640, 0.057950, 0.032010, 0.014700,
        0.004900, 0.002400, 0.009300, 0.029100, 0.063270, 0.109600, 0.165500, 0.225750,
        0.290400, 0.359700, 0.433450, 0.512050, 0.594500, 0.678400, 0.762100, 0.842500,
        0.916300, 0.978600, 1.026300, 1.056700, 1.062200, 1.045600, 1.002600, 0.938400,
        0.854450, 0.751400, 0.642400, 0.541900, 0.447900, 0.360800, 0.283500, 0.218700,
        0.164900, 0.121200, 0.087400, 0.063600, 0.046770, 0.032900, 0.022700, 0.015840,
        0.011359, 0.008111, 0.005790, 0.004109, 0.002929, 0.002091, 0.001484, 0.001047,
        0.000740, 0.000520, 0.000361, 0.000249, 0.000172, 0.000120, 0.000085, 0.000060,
        0.000042
    ])
    
    y_bar = np.array([
        0.000039, 0.000064, 0.000120, 0.000217, 0.000396, 0.000640, 0.001210, 0.002180,
        0.004000, 0.007300, 0.011600, 0.016840, 0.023000, 0.029800, 0.038000, 0.048000,
        0.060000, 0.073900, 0.090980, 0.112600, 0.139020, 0.169300, 0.208020, 0.258600,
        0.323000, 0.407300, 0.503000, 0.608200, 0.710000, 0.793200, 0.862000, 0.914850,
        0.954000, 0.980300, 0.994950, 1.000000, 0.995000, 0.978600, 0.952000, 0.915400,
        0.870000, 0.816300, 0.757000, 0.694900, 0.631000, 0.566800, 0.503000, 0.441200,
        0.381000, 0.321000, 0.265000, 0.217000, 0.175000, 0.138200, 0.107000, 0.081600,
        0.061000, 0.044580, 0.032000, 0.023200, 0.017000, 0.011920, 0.008210, 0.005723,
        0.004102, 0.002929, 0.002091, 0.001484, 0.001047, 0.000740, 0.000520, 0.000361,
        0.000249, 0.000172, 0.000120, 0.000085, 0.000060, 0.000042, 0.000030, 0.000021,
        0.000015
    ])
    
    z_bar = np.array([
        0.006450, 0.010550, 0.020050, 0.036210, 0.067850, 0.110200, 0.207400, 0.371300,
        0.645600, 1.039050, 1.385600, 1.622960, 1.747060, 1.782600, 1.772110, 1.744100,
        1.669200, 1.528100, 1.287640, 1.041900, 0.812950, 0.616200, 0.465180, 0.353300,
        0.272000, 0.212300, 0.158200, 0.111700, 0.078250, 0.057250, 0.042160, 0.029840,
        0.020300, 0.013400, 0.008750, 0.005750, 0.003900, 0.002750, 0.002100, 0.001800,
        0.001650, 0.001400, 0.001100, 0.001000, 0.000800, 0.000600, 0.000340, 0.000240,
        0.000190, 0.000100, 0.000050, 0.000030, 0.000020, 0.000010, 0.000000, 0.000000,
        0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000,
        0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000,
        0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000,
        0.000000
    ])
    
    return wavelengths, x_bar, y_bar, z_bar

# 1nm 간격으로 부드러운 보간
def interpolate_to_1nm(wavelengths_5nm, x_bar_5nm, y_bar_5nm, z_bar_5nm):
    """5nm 데이터를 1nm로 부드러운 3차 보간"""
    wavelengths_1nm = np.arange(380, 781, 1)
    
    # 3차 스플라인 보간으로 매끄러운 곡선 생성
    f_x = interp1d(wavelengths_5nm, x_bar_5nm, kind='cubic', bounds_error=False, fill_value=0)
    f_y = interp1d(wavelengths_5nm, y_bar_5nm, kind='cubic', bounds_error=False, fill_value=0)
    f_z = interp1d(wavelengths_5nm, z_bar_5nm, kind='cubic', bounds_error=False, fill_value=0)
    
    x_bar_1nm = f_x(wavelengths_1nm)
    y_bar_1nm = f_y(wavelengths_1nm)
    z_bar_1nm = f_z(wavelengths_1nm)
    
    # 음수 값 제거
    x_bar_1nm = np.maximum(x_bar_1nm, 0)
    y_bar_1nm = np.maximum(y_bar_1nm, 0)
    z_bar_1nm = np.maximum(z_bar_1nm, 0)
    
    return wavelengths_1nm, x_bar_1nm, y_bar_1nm, z_bar_1nm

# 데이터 생성
wavelengths_5nm, x_bar_5nm, y_bar_5nm, z_bar_5nm = get_standard_cie1931_data()
wavelengths_1nm, x_bar_1nm, y_bar_1nm, z_bar_1nm = interpolate_to_1nm(wavelengths_5nm, x_bar_5nm, y_bar_5nm, z_bar_5nm)

print(f"1nm 데이터 생성 완료: {len(wavelengths_1nm)}개 파장점 (380-780nm)")

# 스펙트럼 궤적 계산
def calculate_spectral_locus():
    """1nm 정밀도 스펙트럼 궤적 계산"""
    spectral_x = []
    spectral_y = []
    valid_wavelengths = []
    
    for i, wl in enumerate(wavelengths_1nm):
        X = x_bar_1nm[i]
        Y = y_bar_1nm[i]
        Z = z_bar_1nm[i]
        total = X + Y + Z
        
        if total > 1e-10:
            x = X / total
            y = Y / total
            spectral_x.append(x)
            spectral_y.append(y)
            valid_wavelengths.append(wl)
    
    return np.array(spectral_x), np.array(spectral_y), valid_wavelengths

spectral_x, spectral_y, valid_wavelengths = calculate_spectral_locus()

print(f"스펙트럼 궤적 계산 완료: {len(spectral_x)}개 점")
print(f"x 범위: [{np.min(spectral_x):.4f}, {np.max(spectral_x):.4f}]")
print(f"y 범위: [{np.min(spectral_y):.4f}, {np.max(spectral_y):.4f}]")

# 완전한 경계 생성 (380nm-780nm 전체 범위) - 더 매끄럽게
def create_complete_boundary():
    """완전한 말발굽 경계 생성 - 매끄러운 자홍선"""
    boundary_points = []
    
    # 1. 스펙트럼 궤적 전체 (380nm → 780nm)
    for i in range(len(spectral_x)):
        boundary_points.append([spectral_x[i], spectral_y[i]])
    
    # 2. 자홍선 (780nm → 380nm) - 더 많은 점으로 매끄럽게
    if len(spectral_x) >= 2:
        start_point = [spectral_x[-1], spectral_y[-1]]  # 780nm
        end_point = [spectral_x[0], spectral_y[0]]      # 380nm
        
        # 자홍선을 100개 점으로 매끄럽게 분할
        purple_steps = 100
        for i in range(1, purple_steps):
            t = i / purple_steps
            purple_x = start_point[0] * (1-t) + end_point[0] * t
            purple_y = start_point[1] * (1-t) + end_point[1] * t
            boundary_points.append([purple_x, purple_y])
    
    return np.array(boundary_points)

boundary_points = create_complete_boundary()
print(f"경계 다각형 생성 완료: {len(boundary_points)}개 점")

# CIE 1976 변환
def xy_to_uv_1976(x, y):
    """CIE 1931 xy → CIE 1976 u'v' 변환"""
    denom = -2*x + 12*y + 3
    if abs(denom) < 1e-12:
        return None, None
    u_prime = 4*x / denom
    v_prime = 9*y / denom
    return u_prime, v_prime

def uv_1976_to_xy(u_prime, v_prime):
    """CIE 1976 u'v' → CIE 1931 xy 변환"""
    denom = 6*u_prime - 16*v_prime + 12
    if abs(denom) < 1e-12:
        return None, None
    x = 9*u_prime / denom
    y = 4*v_prime / denom
    return x, y

# CIE 1976 경계 생성
uv_boundary_points = []
for point in boundary_points:
    x, y = point[0], point[1]
    u, v = xy_to_uv_1976(x, y)
    if u is not None and v is not None:
        uv_boundary_points.append([u, v])

uv_boundary_points = np.array(uv_boundary_points)
print(f"CIE 1976 경계 생성 완료: {len(uv_boundary_points)}개 점")

# 개선된 sRGB 변환
def xy_to_srgb(x, y):
    """CIE xy → sRGB 변환 (단순화된 안정적 버전)"""
    if y <= 1e-6:
        return [1, 1, 1]
    
    z = max(0, 1 - x - y)
    Y = 1.0
    X = x * Y / y
    Z = z * Y / y
    
    # sRGB 변환 매트릭스
    rgb_linear = np.array([
        [ 3.2406, -1.5372, -0.4986],
        [-0.9689,  1.8758,  0.0415],
        [ 0.0557, -0.2040,  1.0570]
    ]) @ np.array([X, Y, Z])
    
    # 음수 클리핑 및 정규화
    rgb_linear = np.clip(rgb_linear, 0, None)
    max_val = np.max(rgb_linear)
    if max_val > 1:
        rgb_linear = rgb_linear / max_val
    
    # 감마 보정
    rgb_srgb = np.where(rgb_linear <= 0.0031308, 
                       12.92 * rgb_linear, 
                       1.055 * np.power(rgb_linear, 1/2.4) - 0.055)
    
    return np.clip(rgb_srgb, 0, 1)

# 고해상도 색상 맵 생성 (좌표계 매핑 완전 수정)
def create_colormap(x_range, y_range, resolution=1500):
    """고해상도 색상 맵 생성 - 좌표계 매핑 완전 수정"""
    width, height = resolution, resolution
    color_map = np.ones((height, width, 3))
    
    if len(boundary_points) < 3:
        return color_map
    
    path = Path(boundary_points)
    
    # 배열 인덱스와 matplotlib 좌표의 정확한 대응
    for i in range(height):
        if i % (height // 10) == 0:
            print(f"색상 맵 생성 진행률: {i/height*100:.1f}%")
        
        for j in range(width):
            # matplotlib 좌표 계산 (경계선과 동일한 좌표계)
            x = x_range[0] + (j / (width-1)) * (x_range[1] - x_range[0])
            y = y_range[0] + (i / (height-1)) * (y_range[1] - y_range[0])
            
            if path.contains_point([x, y]) and y > 0.001:
                rgb = xy_to_srgb(x, y)
                # 배열 저장: i=0은 y 최소값, 그대로 color_map[i,j]에 저장
                color_map[i, j] = rgb
    
    return color_map

# CIE 1931 다이어그램 생성
print("\n=== CIE 1931 다이어그램 생성 ===")
x_range = [0, 0.8]
y_range = [0, 0.9]
colormap_1931 = create_colormap(x_range, y_range)

fig, ax = plt.subplots(figsize=(12, 12), dpi=300)

ax.imshow(colormap_1931, extent=[x_range[0], x_range[1], y_range[0], y_range[1]], 
          origin='lower', aspect='auto', interpolation='bilinear')

# 스펙트럼 궤적
ax.plot(spectral_x, spectral_y, 'k-', linewidth=3, label='Spectral Locus', zorder=10)

# 자홍선
if len(spectral_x) >= 2:
    ax.plot([spectral_x[-1], spectral_x[0]], [spectral_y[-1], spectral_y[0]], 
            'k--', linewidth=3, label='Purple Line', zorder=10)

# 파장 라벨
major_wavelengths = [400, 450, 500, 520, 550, 570, 600, 650, 700]
for wl in major_wavelengths:
    if wl in valid_wavelengths:
        idx = valid_wavelengths.index(wl)
        ax.annotate(f'{wl}nm', (spectral_x[idx], spectral_y[idx]), 
                   xytext=(8, 8), textcoords='offset points', 
                   fontsize=10, fontweight='bold', color='white',
                   bbox=dict(boxstyle="round,pad=0.3", facecolor='black', alpha=0.8))

# 등에너지 백색점
ax.plot(1/3, 1/3, 'wo', markersize=10, markeredgecolor='black', 
        markeredgewidth=2, label='Equal Energy White', zorder=10)

ax.set_xlim(0, 0.8)
ax.set_ylim(0, 0.9)
ax.set_xlabel('CIE x', fontsize=14, fontweight='bold')
ax.set_ylabel('CIE y', fontsize=14, fontweight='bold')
ax.set_title('CIE 1931 Chromaticity Diagram (Corrected)', fontsize=16, fontweight='bold')
ax.grid(True, alpha=0.3)
ax.legend(fontsize=12)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "cie1931_corrected.png"), dpi=300, bbox_inches='tight')
plt.close()

# CIE 1976 다이어그램 생성
print("\n=== CIE 1976 다이어그램 생성 ===")

def create_uv_colormap(u_range, v_range, resolution=1500):
    """CIE 1976 색상 맵 생성 - 좌표계 매핑 완전 수정"""
    width, height = resolution, resolution
    color_map = np.ones((height, width, 3))
    
    if len(uv_boundary_points) < 3:
        return color_map
    
    path = Path(uv_boundary_points)
    
    # 배열 인덱스와 matplotlib 좌표의 정확한 대응
    for i in range(height):
        if i % (height // 10) == 0:
            print(f"CIE 1976 색상 맵 생성 진행률: {i/height*100:.1f}%")
        
        for j in range(width):
            # matplotlib 좌표 계산 (경계선과 동일한 좌표계)
            u = u_range[0] + (j / (width-1)) * (u_range[1] - u_range[0])
            v = v_range[0] + (i / (height-1)) * (v_range[1] - v_range[0])
            
            if path.contains_point([u, v]):
                x, y = uv_1976_to_xy(u, v)
                if x is not None and y is not None and y > 0.001:
                    rgb = xy_to_srgb(x, y)
                    # 배열 저장: i=0은 v 최소값, 그대로 color_map[i,j]에 저장
                    color_map[i, j] = rgb
    
    return color_map

u_range = [0, 0.7]
v_range = [0, 0.6]
colormap_1976 = create_uv_colormap(u_range, v_range)

fig, ax = plt.subplots(figsize=(12, 12), dpi=300)

ax.imshow(colormap_1976, extent=[u_range[0], u_range[1], v_range[0], v_range[1]], 
          origin='lower', aspect='auto', interpolation='bilinear')

# CIE 1976 스펙트럼 궤적
uv_spectral_x = []
uv_spectral_y = []
for i in range(len(spectral_x)):
    u, v = xy_to_uv_1976(spectral_x[i], spectral_y[i])
    if u is not None and v is not None:
        uv_spectral_x.append(u)
        uv_spectral_y.append(v)

uv_spectral_x = np.array(uv_spectral_x)
uv_spectral_y = np.array(uv_spectral_y)

ax.plot(uv_spectral_x, uv_spectral_y, 'k-', linewidth=3, label='Spectral Locus', zorder=10)

# 자홍선
if len(uv_spectral_x) >= 2:
    ax.plot([uv_spectral_x[-1], uv_spectral_x[0]], [uv_spectral_y[-1], uv_spectral_y[0]], 
            'k--', linewidth=3, label='Purple Line', zorder=10)

# 파장 라벨
for wl in major_wavelengths:
    if wl in valid_wavelengths:
        idx = valid_wavelengths.index(wl)
        u, v = xy_to_uv_1976(spectral_x[idx], spectral_y[idx])
        if u is not None and v is not None:
            ax.annotate(f'{wl}nm', (u, v), 
                       xytext=(8, 8), textcoords='offset points', 
                       fontsize=10, fontweight='bold', color='white',
                       bbox=dict(boxstyle="round,pad=0.3", facecolor='black', alpha=0.8))

# 등에너지 백색점
u_white, v_white = xy_to_uv_1976(1/3, 1/3)
if u_white is not None and v_white is not None:
    ax.plot(u_white, v_white, 'wo', markersize=10, markeredgecolor='black', 
            markeredgewidth=2, label='Equal Energy White', zorder=10)

ax.set_xlim(0, 0.7)
ax.set_ylim(0, 0.6)
ax.set_xlabel("CIE u'", fontsize=14, fontweight='bold')
ax.set_ylabel("CIE v'", fontsize=14, fontweight='bold')
ax.set_title('CIE 1976 UCS Chromaticity Diagram (Corrected)', fontsize=16, fontweight='bold')
ax.grid(True, alpha=0.3)
ax.legend(fontsize=12)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "cie1976_corrected.png"), dpi=300, bbox_inches='tight')
plt.close()

print(f"\n=== 최종 결과 ===")
print(f"저장 위치: {output_dir}")
print("- cie1931_corrected.png: 수정된 CIE 1931")
print("- cie1976_corrected.png: 수정된 CIE 1976")
print(f"파장 범위: {min(valid_wavelengths)}-{max(valid_wavelengths)}nm")
print(f"해상도: 1500x1500")
print("표준 CIE 데이터 기반으로 완전히 재구성 완료!")