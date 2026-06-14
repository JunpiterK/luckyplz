import os
import sys
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QCheckBox, QFileDialog, QStatusBar, QSplitter, QSlider, QLabel, QDialog
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import pandas as pd
import numpy as np
from scipy.interpolate import interp1d
from matplotlib.patches import Rectangle

# 전역 변수 - 상수화
file_path = None
data = None
csv_loaded = False
ANGLES = [0, 15, 30, 45, 60]
COLORS = ['blue', 'green', 'red', 'purple', 'orange']
TRANSITION_COLORS = ['darkorange', 'darkred', 'darkgreen', 'darkblue', 'darkviolet']

# 표준 CIE 데이터 - 한 번만 계산하도록 캐시
_cie_data_cache = None
_spectral_locus_cache = None
_blackbody_locus_cache = None

def get_standard_cie1931_data():
    """표준 CIE 1931 색 매칭 함수 데이터 (5nm 간격) - 캐시 사용"""
    global _cie_data_cache
    if _cie_data_cache is not None:
        return _cie_data_cache
    
    wavelengths = np.arange(380, 785, 5)
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
    _cie_data_cache = (wavelengths, x_bar, y_bar, z_bar)
    return _cie_data_cache

def calculate_spectral_locus():
    """부드러운 스펙트럼 궤적 계산 - 캐시 사용"""
    global _spectral_locus_cache
    if _spectral_locus_cache is not None:
        return _spectral_locus_cache
        
    wavelengths_5nm, x_bar_5nm, y_bar_5nm, z_bar_5nm = get_standard_cie1931_data()
    wavelengths_1nm = np.arange(380, 781, 1)
    
    # 3차 보간을 한 번에 처리
    for kind_data, bar_5nm in [('x', x_bar_5nm), ('y', y_bar_5nm), ('z', z_bar_5nm)]:
        f = interp1d(wavelengths_5nm, bar_5nm, kind='cubic', bounds_error=False, fill_value=0)
        bar_1nm = np.maximum(f(wavelengths_1nm), 0)
        if kind_data == 'x': x_bar_1nm = bar_1nm
        elif kind_data == 'y': y_bar_1nm = bar_1nm  
        else: z_bar_1nm = bar_1nm
    
    # 벡터화된 계산
    total = x_bar_1nm + y_bar_1nm + z_bar_1nm
    valid_mask = total > 1e-10
    spectral_x = np.divide(x_bar_1nm, total, out=np.zeros_like(x_bar_1nm), where=valid_mask)[valid_mask]
    spectral_y = np.divide(y_bar_1nm, total, out=np.zeros_like(y_bar_1nm), where=valid_mask)[valid_mask]
    
    _spectral_locus_cache = (spectral_x, spectral_y)
    return _spectral_locus_cache

def calculate_blackbody_locus():
    """Blackbody locus 계산 - 플랑크 법칙 사용"""
    global _blackbody_locus_cache
    if _blackbody_locus_cache is not None:
        return _blackbody_locus_cache
    
    # 물리 상수
    h = 6.626e-34  # 플랑크 상수 (J·s)
    c = 2.998e8    # 빛의 속도 (m/s)
    k = 1.381e-23  # 볼츠만 상수 (J/K)
    
    # 온도 범위 (K) - 더 세밀하게
    temperatures = np.arange(1000, 25000, 50)
    
    # CIE 색 매칭 함수 데이터
    wavelengths, x_bar, y_bar, z_bar = get_standard_cie1931_data()
    wavelengths_m = wavelengths * 1e-9  # nm to m
    
    bb_x, bb_y, bb_u, bb_v = [], [], [], []
    bb_temps = []
    
    for T in temperatures:
        # 플랑크 분포 계산
        exp_term = h * c / (wavelengths_m * k * T)
        # overflow 방지
        exp_term = np.clip(exp_term, 0, 700)
        planck = (2 * h * c**2 / wavelengths_m**5) / (np.exp(exp_term) - 1)
        
        # XYZ 계산 (수치 적분)
        X = np.trapz(planck * x_bar, wavelengths_m)
        Y = np.trapz(planck * y_bar, wavelengths_m)
        Z = np.trapz(planck * z_bar, wavelengths_m)
        
        # 정규화
        total = X + Y + Z
        if total > 1e-10:
            x = X / total
            y = Y / total
            
            # CIE 1976 변환
            denom = X + 15*Y + 3*Z
            if denom > 1e-10:
                u_prime = 4*X / denom
                v_prime = 9*Y / denom
                
                bb_x.append(x)
                bb_y.append(y)
                bb_u.append(u_prime)
                v_prime_val = 9*Y / denom
                bb_v.append(v_prime_val)
                bb_temps.append(T)
    
    _blackbody_locus_cache = (bb_x, bb_y, bb_u, bb_v, bb_temps)
    return _blackbody_locus_cache

def get_duv_lines_for_range(x_range, y_range, u_range, v_range, interval):
    """축 범위와 선택된 간격에 따라 적절한 DUV 라인 생성"""
    bb_x, bb_y, bb_u, bb_v, bb_temps = calculate_blackbody_locus()
    
    # 축 범위 크기에 따라 온도 간격 결정 (6500K 중심으로)
    x_span = x_range[1] - x_range[0]
    y_span = y_range[1] - y_range[0]
    u_span = u_range[1] - u_range[0]
    v_span = v_range[1] - v_range[0]
    
    # 6500K를 중심으로 위아래로 온도 목록 생성
    center_temp = 6500
    temp_labels = []
    
    # 중심 온도 추가
    temp_labels.append(center_temp)
    
    # 위아래로 온도 추가 (대략 1000K ~ 20000K 범위)
    for i in range(1, 20):
        # 위로
        upper_temp = center_temp + (interval * i)
        if upper_temp <= 20000:
            temp_labels.append(upper_temp)
        
        # 아래로
        lower_temp = center_temp - (interval * i)
        if lower_temp >= 1000:
            temp_labels.append(lower_temp)
    
    # 정렬
    temp_labels.sort()
    
    # 확대된 상태에서는 더 촘촘하게
    if x_span < 0.3 or y_span < 0.3 or u_span < 0.3 or v_span < 0.3:
        # 매우 확대된 상태 - 간격을 절반으로
        fine_temp_labels = []
        fine_temp_labels.append(center_temp)
        
        for i in range(1, 40):
            upper_temp = center_temp + (interval * i // 2)
            if upper_temp <= 20000:
                fine_temp_labels.append(upper_temp)
            
            lower_temp = center_temp - (interval * i // 2)
            if lower_temp >= 1000:
                fine_temp_labels.append(lower_temp)
        
        temp_labels = sorted(fine_temp_labels)
    
    label_data = []
    duv_lines_1931 = []
    duv_lines_1976 = []
    
    for temp in temp_labels:
        if temp >= min(bb_temps) and temp <= max(bb_temps):
            idx = np.argmin(np.abs(np.array(bb_temps) - temp))
            if idx > 0 and idx < len(bb_x)-1:  # 접선 계산을 위해 양쪽 점이 필요
                # 접선 기울기 계산 (중앙 차분)
                dx_dt_1931 = (bb_x[idx+1] - bb_x[idx-1]) / (bb_temps[idx+1] - bb_temps[idx-1])
                dy_dt_1931 = (bb_y[idx+1] - bb_y[idx-1]) / (bb_temps[idx+1] - bb_temps[idx-1])
                
                du_dt_1976 = (bb_u[idx+1] - bb_u[idx-1]) / (bb_temps[idx+1] - bb_temps[idx-1])
                dv_dt_1976 = (bb_v[idx+1] - bb_v[idx-1]) / (bb_temps[idx+1] - bb_temps[idx-1])
                
                # 접선 벡터 정규화
                tangent_norm_1931 = np.sqrt(dx_dt_1931**2 + dy_dt_1931**2)
                tangent_norm_1976 = np.sqrt(du_dt_1976**2 + dv_dt_1976**2)
                
                if tangent_norm_1931 > 1e-10 and tangent_norm_1976 > 1e-10:
                    # 정규화된 수직 벡터 계산
                    perp_x_1931 = -dy_dt_1931 / tangent_norm_1931
                    perp_y_1931 = dx_dt_1931 / tangent_norm_1931
                    
                    perp_u_1976 = -dv_dt_1976 / tangent_norm_1976
                    perp_v_1976 = du_dt_1976 / tangent_norm_1976
                    
                    # Duv 라인 길이 (축 범위에 따라 조정) - 절반으로 줄임
                    line_length_1931 = min(x_span, y_span) * 0.075
                    line_length_1976 = min(u_span, v_span) * 0.075
                    
                    # CIE 1931 Duv 라인
                    x_center, y_center = bb_x[idx], bb_y[idx]
                    x1 = x_center - line_length_1931 * perp_x_1931
                    y1 = y_center - line_length_1931 * perp_y_1931
                    x2 = x_center + line_length_1931 * perp_x_1931
                    y2 = y_center + line_length_1931 * perp_y_1931
                    duv_lines_1931.append((x1, y1, x2, y2))
                    
                    # CIE 1976 Duv 라인
                    u_center, v_center = bb_u[idx], bb_v[idx]
                    u1 = u_center - line_length_1976 * perp_u_1976
                    v1 = v_center - line_length_1976 * perp_v_1976
                    u2 = u_center + line_length_1976 * perp_u_1976
                    v2 = v_center + line_length_1976 * perp_v_1976
                    duv_lines_1976.append((u1, v1, u2, v2))
                    
                    # 온도 라벨 표시 규칙
                    show_label = False
                    
                    if interval <= 500:
                        # 작은 간격일 때는 주요 온도만 표시 (6500K 중심으로)
                        key_temps = [2000, 3000, 4000, 5000, 6500, 8000, 10000, 15000]
                        if temp in key_temps:
                            show_label = True
                    else:
                        # 큰 간격일 때는 더 많이 표시
                        key_temps = [1500, 2000, 2500, 3000, 4000, 5000, 6500, 8000, 10000, 15000, 20000]
                        if temp in key_temps:
                            show_label = True
                    
                    if show_label:
                        label_data.append({
                            'temp': temp,
                            'x': bb_x[idx], 'y': bb_y[idx],
                            'u': bb_u[idx], 'v': bb_v[idx]
                        })
    
    return label_data, duv_lines_1931, duv_lines_1976

# 벡터화된 색공간 변환 함수들
def xy_to_uv_vectorized(x, y):
    """벡터화된 CIE1931 → CIE1976 변환"""
    denom = -2 * x + 12 * y + 3
    valid_mask = np.abs(denom) >= 1e-12
    u_prime = np.divide(4 * x, denom, out=np.full_like(x, np.nan), where=valid_mask)
    v_prime = np.divide(9 * y, denom, out=np.full_like(y, np.nan), where=valid_mask)
    return u_prime, v_prime

def xy_to_uv(x, y):
    """단일 값 변환"""
    denom = -2 * x + 12 * y + 3
    return (4 * x / denom, 9 * y / denom) if abs(denom) >= 1e-12 else (None, None)

def xy_to_XYZ(x, y):
    """xy → XYZ 변환"""
    if y == 0: return (0, 0, 0)
    Y = 1.0
    return (x * Y / y, Y, (1 - x - y) * Y / y)

def XYZ_to_Lab(X, Y, Z):
    """XYZ → Lab 변환"""
    Xn, Yn, Zn = 0.95047, 1.00000, 1.08883
    fx = np.cbrt(X/Xn) if X/Xn > (6/29)**3 else X/(3*(6/29)**2*Xn) + 4/29
    fy = np.cbrt(Y/Yn) if Y/Yn > (6/29)**3 else Y/(3*(6/29)**2*Yn) + 4/29
    fz = np.cbrt(Z/Zn) if Z/Zn > (6/29)**3 else Z/(3*(6/29)**2*Zn) + 4/29
    return (116*fy - 16, 500*(fx - fy), 200*(fy - fz))

def deltaE2000(Lab1, Lab2):
    """CIEDE2000 구현 - 단순화"""
    L1,a1,b1 = Lab1; L2,a2,b2 = Lab2
    avg_L = (L1+L2)/2
    C1 = np.hypot(a1, b1); C2 = np.hypot(a2, b2)
    avg_C = (C1+C2)/2
    G = 0.5*(1 - np.sqrt((avg_C**7)/(avg_C**7 + 25**7)))
    a1p = (1+G)*a1; a2p = (1+G)*a2
    C1p = np.hypot(a1p, b1); C2p = np.hypot(a2p, b2)
    h1p = np.degrees(np.arctan2(b1, a1p)) % 360
    h2p = np.degrees(np.arctan2(b2, a2p)) % 360
    dLp = L2 - L1; dCp = C2p - C1p
    dhp = h2p - h1p
    dhp -= 360 * (dhp > 180); dhp += 360 * (dhp < -180)
    dHp = 2 * np.sqrt(C1p*C2p) * np.sin(np.radians(dhp)/2)
    avg_Lp = (L1+L2)/2; avg_Cp = (C1p+C2p)/2
    hp_sum = h1p+h2p
    avg_hp = (hp_sum+360)/2 if np.abs(h1p-h2p)>180 else hp_sum/2
    T = 1 - 0.17*np.cos(np.radians(avg_hp-30)) + 0.24*np.cos(np.radians(2*avg_hp)) + \
        0.32*np.cos(np.radians(3*avg_hp+6)) - 0.20*np.cos(np.radians(4*avg_hp-63))
    dTheta = 30*np.exp(-((avg_hp-275)/25)**2)
    RC = 2*np.sqrt((avg_Cp**7)/(avg_Cp**7+25**7))
    SL = 1 + ((0.015*(avg_Lp-50)**2)/np.sqrt(20+(avg_Lp-50)**2))
    SC = 1 + 0.045*avg_Cp; SH = 1 + 0.015*avg_Cp*T
    RT = -np.sin(2*np.radians(dTheta))*RC
    return np.sqrt((dLp/SL)**2 + (dCp/SC)**2 + (dHp/SH)**2 + RT*(dCp/SC)*(dHp/SH))

def geometric_median(points, tol=1e-5):
    """2D Geometric Median (Weiszfeld) - 최적화"""
    points = np.asarray(points, dtype=float)
    median = np.median(points, axis=0)
    for _ in range(100):  # 최대 반복 횟수 제한
        dist = np.linalg.norm(points - median, axis=1)
        zero_mask = dist == 0
        if np.any(zero_mask): return points[zero_mask][0]
        weights = 1.0/dist
        next_med = np.average(points, axis=0, weights=weights)
        if np.linalg.norm(next_med-median)<tol: return next_med
        median = next_med
    return median

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("설정")
        self.setFixedSize(350, 300)
        self.setModal(True)
        self.parent_window = parent
        
        layout = QVBoxLayout(self)
        
        # 좌표계색보기 체크박스
        self.bg_cb = QCheckBox("좌표계색보기")
        self.bg_cb.setChecked(self.parent_window.show_bg)
        layout.addWidget(self.bg_cb)
        
        # 색좌표경계 체크박스
        self.boundary_cb = QCheckBox("색좌표경계")
        self.boundary_cb.setChecked(self.parent_window.show_boundaries)
        layout.addWidget(self.boundary_cb)
        
        # Blackbody locus 체크박스들
        bb_layout = QVBoxLayout()
        bb_label = QLabel("Blackbody Locus Intervals:")
        bb_layout.addWidget(bb_label)
        
        self.bb_checkboxes = {}
        for interval in [100, 500, 1000, 1500]:
            cb = QCheckBox(f"{interval}K")
            cb.setChecked(self.parent_window.blackbody_intervals[interval])
            self.bb_checkboxes[interval] = cb
            bb_layout.addWidget(cb)
        
        layout.addLayout(bb_layout)
        
        # 좌표계색투명도 슬라이더
        alpha_layout = QHBoxLayout()
        alpha_layout.addWidget(QLabel("좌표계색투명도:"))
        self.alpha_slider = QSlider(Qt.Horizontal)
        self.alpha_slider.setRange(10, 100)
        self.alpha_slider.setValue(self.parent_window.bg_alpha)
        self.alpha_label = QLabel(f"{self.parent_window.bg_alpha}%")
        self.alpha_slider.valueChanged.connect(lambda v: self.alpha_label.setText(f"{v}%"))
        alpha_layout.addWidget(self.alpha_slider)
        alpha_layout.addWidget(self.alpha_label)
        layout.addLayout(alpha_layout)
        
        # 닫기 버튼
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(self.accept_and_close)
        close_layout.addWidget(close_btn)
        layout.addLayout(close_layout)
    
    def accept_and_close(self):
        self.parent_window.show_bg = self.bg_cb.isChecked()
        self.parent_window.show_boundaries = self.boundary_cb.isChecked()
        
        # Blackbody intervals 업데이트
        for interval, cb in self.bb_checkboxes.items():
            self.parent_window.blackbody_intervals[interval] = cb.isChecked()
        
        self.parent_window.bg_alpha = self.alpha_slider.value()
        self.parent_window.preserve_axis_limits = True  # 설정 변경시 축 범위 유지
        self.parent_window.update_plot()
        self.accept()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 기본 설정
        self.setWindowTitle("ColorTrack - VACS Analizer")
        self.setGeometry(100,100,1400,750)
        
        # UI 초기화
        self.central_widget=QWidget(); self.setCentralWidget(self.central_widget)
        self.main_layout=QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 변수 초기화
        self.angle_vars = {a:False for a in ANGLES}
        self.cie1931_bg = self.cie1976_bg = None
        self.show_bg = True; self.show_boundaries = True; self.bg_alpha = 70
        self.blackbody_intervals = {100: False, 500: False, 1000: False, 1500: False}  # 각 간격별 표시 여부
        self.ax1_xlim = self.ax1_ylim = self.ax2_xlim = self.ax2_ylim = None
        self.preserve_axis_limits = False
        self.pan_active = False; self.pan_start = self.pan_ax = None
        self.button_pressed = None; self.old_pos = None
        
        # 좌표 표시용 텍스트 객체들
        self.coord_text1 = None
        self.coord_text2 = None
        
        # 컴포넌트 설정
        self.load_background_images()
        self.setup_control_panel()
        
        # matplotlib 설정 - 모든 폰트 크기 절반으로
        plt.rcParams.update({
            'font.size': 10, 'axes.titlesize': 12, 'axes.labelsize': 10,
            'xtick.labelsize': 9, 'ytick.labelsize': 9, 'legend.fontsize': 8,
        })
        
        # 그래프 초기화
        self.fig = plt.figure(figsize=(14,7))
        self.ax1, self.ax2 = self.fig.add_subplot(121), self.fig.add_subplot(122)
        self.canvas = FigureCanvas(self.fig)
        
        # 툴바 없이 캔버스만 스플리터에 추가
        sp = QSplitter(Qt.Vertical)
        sp.addWidget(self.canvas)
        sp.setSizes([750])  # 캔버스에 충분한 높이 할당
        self.main_layout.addWidget(sp)
        
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - ColorTrack Professional")
        
        # 이벤트 연결
        events = ['scroll_event', 'button_press_event', 'button_release_event', 'motion_notify_event', 'pick_event']
        handlers = [self.on_scroll, self.on_press, self.on_release, self.on_motion, self.on_pick]
        for event, handler in zip(events, handlers):
            self.canvas.mpl_connect(event, handler)
        
        self.update_plot()

    def load_background_images(self):
        """배경 이미지 로드"""
        for fname, target in [
            (["cie1931_background_clean.png", r"C:\non_documents\ColorTrack\cie1931_background_clean.png"], 'cie1931_bg'),
            (["cie1976_background_clean.png", r"C:\non_documents\ColorTrack\cie1976_background_clean.png"], 'cie1976_bg')
        ]:
            for path in fname:
                if os.path.exists(path):
                    setattr(self, target, mpimg.imread(path))
                    break

    def setup_control_panel(self):
        """컨트롤 패널 설정 - 모던 버튼과 체크박스만 적용"""
        p = QWidget()
        lay = QVBoxLayout(p)
        
        # 모던 버튼 스타일
        button_style = """
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #4a90e2, stop: 1 #357abd);
                border: 1px solid #357abd;
                border-radius: 8px;
                color: white;
                font-weight: 600;
                padding: 8px 16px;
                font-size: 11pt;
                min-height: 32px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #5ba0f2, stop: 1 #4a90e2);
                border: 1px solid #4a90e2;
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #357abd, stop: 1 #2e6ba8);
            }
        """
        
        settings_button_style = """
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #ffffff, stop: 1 #f8f9fa);
                border: 1px solid #dee2e6;
                border-radius: 20px;
                color: #6c757d;
                font-size: 14pt;
                font-weight: bold;
                min-width: 38px;
                min-height: 38px;
                padding: 8px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #f8f9fa, stop: 1 #e9ecef);
                border: 1px solid #adb5bd;
                color: #495057;
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #e9ecef, stop: 1 #dee2e6);
            }
        """
        
        # 모던 체크박스 스타일
        checkbox_style = """
            QCheckBox {
                color: #495057;
                spacing: 8px;
                font-size: 11pt;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 3px;
                border: 2px solid #dee2e6;
                background: white;
            }
            QCheckBox::indicator:hover {
                border: 2px solid #4a90e2;
            }
            QCheckBox::indicator:checked {
                background: #4a90e2;
                border: 2px solid #4a90e2;
            }
            QCheckBox::indicator:checked:hover {
                background: #357abd;
                border: 2px solid #357abd;
            }
        """
        
        # 첫 번째 행 - 버튼들
        r1 = QWidget()
        h1 = QHBoxLayout(r1)
        
        load_btn = QPushButton("📁 Load Data")
        load_btn.setStyleSheet(button_style)
        load_btn.clicked.connect(self.select_file)
        h1.addWidget(load_btn)
        
        save_btn = QPushButton("💾 Save Plot")
        save_btn.setStyleSheet(button_style)
        save_btn.clicked.connect(self.save_plot)
        h1.addWidget(save_btn)
        
        settings_btn = QPushButton("⚙")
        settings_btn.setStyleSheet(settings_button_style)
        settings_btn.setToolTip("설정")
        settings_btn.clicked.connect(self.show_settings)
        h1.addWidget(settings_btn)
        
        h1.addStretch()
        lay.addWidget(r1)
        
        # 두 번째 행 - Viewing Angle 체크박스
        r2 = QWidget()
        h2 = QHBoxLayout(r2)
        
        # Viewing Angle 라벨 - 모던하게
        va_label = QLabel("📐 Viewing Angle:")
        va_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        va_label.setStyleSheet("""
            QLabel {
                color: #495057;
                padding: 2px 8px 2px 0px;
                border-bottom: 2px solid #4a90e2;
                margin-right: 12px;
            }
        """)
        h2.addWidget(va_label)
        
        for a in ANGLES:
            cb = QCheckBox(f"{a}°")
            cb.setStyleSheet(checkbox_style)
            cb.stateChanged.connect(lambda s, ang=a: self.toggle_angle(ang, s))
            h2.addWidget(cb)
        
        h2.addStretch()
        lay.addWidget(r2)
        
        # 세 번째 행 - Blackbody Locus 체크박스
        r3 = QWidget()
        h3 = QHBoxLayout(r3)
        
        # Blackbody Locus 라벨 - 모던하게
        bb_label = QLabel("🌡️ Blackbody Locus:")
        bb_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        bb_label.setStyleSheet("""
            QLabel {
                color: #495057;
                padding: 2px 8px 2px 0px;
                border-bottom: 2px solid #e74c3c;
                margin-right: 12px;
            }
        """)
        h3.addWidget(bb_label)
        
        # Blackbody 간격 체크박스들
        self.blackbody_checkboxes = {}
        intervals = [100, 500, 1000, 1500]
        
        for interval in intervals:
            cb = QCheckBox(f"{interval}K")
            cb.setStyleSheet(checkbox_style)
            cb.stateChanged.connect(lambda s, i=interval: self.toggle_blackbody_interval(i, s))
            self.blackbody_checkboxes[interval] = cb
            h3.addWidget(cb)
        
        h3.addStretch()
        lay.addWidget(r3)
        
        self.main_layout.addWidget(p)

    def show_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec_()

    def toggle_angle(self, a, s):
        self.angle_vars[a] = (s == Qt.Checked)
        self.preserve_axis_limits = False
        self.ax1_xlim = self.ax1_ylim = self.ax2_xlim = self.ax2_ylim = None
        self.update_plot()

    def toggle_blackbody_interval(self, interval, s):
        """Blackbody locus 간격별 체크박스 토글"""
        self.blackbody_intervals[interval] = (s == Qt.Checked)
        self.preserve_axis_limits = True  # blackbody는 축 범위를 유지
        self.update_plot()

    def select_file(self):
        global data, csv_loaded
        path, _ = QFileDialog.getOpenFileName(self, "CSV", "", "*.csv")
        if path:
            data = pd.read_csv(path)
            csv_loaded = True
            self.status_bar.showMessage(f"Loaded {os.path.basename(path)} ({len(data)}) rows")
            for cb in self.findChildren(QCheckBox):
                if cb.text().endswith('°'): cb.setChecked(False)
            self.preserve_axis_limits = False
            self.ax1_xlim = self.ax1_ylim = self.ax2_xlim = self.ax2_ylim = None
        else:
            csv_loaded = False
            self.status_bar.showMessage("No file selected")
        self.update_plot()

    def save_plot(self):
        default_path = r"C:\non_documents\ColorTrack\chromaticity_diagrams.png"
        path, _ = QFileDialog.getSaveFileName(self, "Save Plot", default_path, "PNG Files (*.png);;All Files (*)")
        if path:
            try:
                self.fig.tight_layout()
                self.fig.subplots_adjust(left=0.05, right=0.95, wspace=0.2)
                self.fig.savefig(path, dpi=300, bbox_inches='tight')
                self.status_bar.showMessage(f"Plot saved to {path}")
            except Exception as e:
                self.status_bar.showMessage(f"Error saving plot: {str(e)}")
        else:
            self.status_bar.showMessage("Save plot cancelled")
    
    def update_coordinate_display(self, event):
        """각 그래프의 왼쪽 아래에 마우스 좌표 표시"""
        # 기존 좌표 텍스트 제거
        if self.coord_text1:
            self.coord_text1.remove()
            self.coord_text1 = None
        if self.coord_text2:
            self.coord_text2.remove()
            self.coord_text2 = None
        
        # 그래프 영역 밖이면 아무것도 표시하지 않음
        if event.inaxes not in [self.ax1, self.ax2] or event.xdata is None or event.ydata is None:
            self.canvas.draw_idle()
            return
        
        # legend와 동일한 스타일로 좌표 텍스트 설정 - 크기 절반으로
        coord_style = {
            'bbox': dict(boxstyle='round,pad=0.15', facecolor='white', alpha=0.95, 
                        edgecolor='#ccc', linewidth=0.5),  # pad 절반으로
            'fontsize': 8,  # 16 → 8로 절반
            'fontweight': 'normal',
            'color': '#000000',
            'ha': 'left',
            'va': 'bottom',
            'zorder': 100
        }
        
        if event.inaxes == self.ax1:
            # CIE 1931 좌표 표시
            coord_text = f"x: {event.xdata:.4f}\ny: {event.ydata:.4f}"
            coord_style['transform'] = self.ax1.transAxes
            self.coord_text1 = self.ax1.text(0.02, 0.02, coord_text, **coord_style)
            
        elif event.inaxes == self.ax2:
            # CIE 1976 좌표 표시
            coord_text = f"u': {event.xdata:.4f}\nv': {event.ydata:.4f}"
            coord_style['transform'] = self.ax2.transAxes
            self.coord_text2 = self.ax2.text(0.02, 0.02, coord_text, **coord_style)
        
        # 화면 업데이트
        self.canvas.draw_idle()
    
    # 네비게이션 이벤트 핸들러들 - 통합 및 최적화
    def on_scroll(self, event):
        if event.inaxes not in [self.ax1, self.ax2]: return
        factor = 0.9 if event.step > 0 else 1.1
        xlim, ylim = event.inaxes.get_xlim(), event.inaxes.get_ylim()
        x_center = event.xdata if event.xdata else (xlim[0] + xlim[1]) / 2
        y_center = event.ydata if event.ydata else (ylim[0] + ylim[1]) / 2
        x_range, y_range = (xlim[1] - xlim[0]) * factor / 2, (ylim[1] - ylim[0]) * factor / 2
        event.inaxes.set_xlim(x_center - x_range, x_center + x_range)
        event.inaxes.set_ylim(y_center - y_range, y_center + y_range)
        self.save_axis_limits()
        self.canvas.draw_idle()

    def on_press(self, event):
        if event.inaxes in [self.ax1, self.ax2] and event.button in [1, 3]:
            self.pan_active, self.pan_start, self.pan_ax = True, (event.xdata, event.ydata), event.inaxes

    def on_release(self, event):
        if self.pan_active: self.save_axis_limits()
        self.pan_active = self.pan_start = self.pan_ax = None

    def on_motion(self, event):
        # 좌표 표시 업데이트
        self.update_coordinate_display(event)
        
        # 팬 동작
        if self.pan_active and self.pan_start and event.inaxes == self.pan_ax and event.xdata and event.ydata:
            dx, dy = self.pan_start[0] - event.xdata, self.pan_start[1] - event.ydata
            xlim, ylim = self.pan_ax.get_xlim(), self.pan_ax.get_ylim()
            self.pan_ax.set_xlim(xlim[0] + dx, xlim[1] + dx)
            self.pan_ax.set_ylim(ylim[0] + dy, ylim[1] + dy)
            self.canvas.draw_idle()

    def on_pick(self, event):
        if not (hasattr(event.artist, 'get_gid') and event.artist.get_gid()): return
        gid = event.artist.get_gid()
        self.button_pressed = gid
        self.redraw_navigation_buttons()
        QTimer.singleShot(150, self.release_button)
        
        # 버튼 액션 매핑
        actions = {
            'zoom_in_1': (self.ax1, 0.8), 'zoom_out_1': (self.ax1, 1.25), 'home_1': (self.ax1, None),
            'zoom_in_2': (self.ax2, 0.8), 'zoom_out_2': (self.ax2, 1.25), 'home_2': (self.ax2, None)
        }
        if gid in actions:
            ax, factor = actions[gid]
            self.home_to_data(ax) if factor is None else self.zoom_axis(ax, factor)

    def release_button(self):
        self.button_pressed = None
        self.redraw_navigation_buttons()

    def save_axis_limits(self):
        self.ax1_xlim, self.ax1_ylim = self.ax1.get_xlim(), self.ax1.get_ylim()
        self.ax2_xlim, self.ax2_ylim = self.ax2.get_xlim(), self.ax2.get_ylim()
        self.preserve_axis_limits = True

    def home_to_data(self, ax):
        global csv_loaded, data
        if not (csv_loaded and data is not None): return self.reset_axis(ax)
        
        sel = [a for a, v in self.angle_vars.items() if v]
        if not sel: return self.reset_axis(ax)
        
        all_x, all_y = [], []
        for a in sel:
            all_x.extend(data[f"{a}_x"].values)
            all_y.extend(data[f"{a}_y"].values)
        
        if not (all_x and all_y): return self.reset_axis(ax)
        
        margin = 0.1
        x_min, x_max, y_min, y_max = min(all_x), max(all_x), min(all_y), max(all_y)
        x_range, y_range = x_max - x_min, y_max - y_min
        
        if ax == self.ax1:
            ax.set_xlim(max(0, x_min - x_range * margin), min(0.8, x_max + x_range * margin))
            ax.set_ylim(max(0, y_min - y_range * margin), min(0.9, y_max + y_range * margin))
        else:  # ax2
            uv_coords = [(u, v) for x, y in zip(all_x, all_y) 
                        for u, v in [xy_to_uv(x, y)] if u is not None]
            if uv_coords:
                u_vals, v_vals = zip(*uv_coords)
                u_min, u_max, v_min, v_max = min(u_vals), max(u_vals), min(v_vals), max(v_vals)
                u_range, v_range = u_max - u_min, v_max - v_min
                ax.set_xlim(max(0, u_min - u_range * margin), min(0.7, u_max + u_range * margin))
                ax.set_ylim(max(0, v_min - v_range * margin), min(0.6, v_max + v_range * margin))
        
        self.save_axis_limits()
        self.canvas.draw_idle()

    def zoom_axis(self, ax, factor):
        xlim, ylim = ax.get_xlim(), ax.get_ylim()
        x_center, y_center = (xlim[0] + xlim[1]) / 2, (ylim[0] + ylim[1]) / 2
        x_range, y_range = (xlim[1] - xlim[0]) * factor / 2, (ylim[1] - ylim[0]) * factor / 2
        ax.set_xlim(x_center - x_range, x_center + x_range)
        ax.set_ylim(y_center - y_range, y_center + y_range)
        self.save_axis_limits()
        self.canvas.draw_idle()

    def reset_axis(self, ax):
        if ax == self.ax1: ax.set_xlim(0, 0.8); ax.set_ylim(0, 0.9)
        else: ax.set_xlim(0, 0.7); ax.set_ylim(0, 0.6)
        self.save_axis_limits()
        self.canvas.draw_idle()

    def redraw_navigation_buttons(self):
        """네비게이션 버튼만 효율적으로 다시 그리기"""
        for ax in [self.ax1, self.ax2]:
            # 버튼 관련 요소만 제거
            to_remove = [child for child in ax.get_children() 
                        if (hasattr(child, 'get_gid') and child.get_gid() and 
                            ('zoom' in child.get_gid() or 'home' in child.get_gid())) or
                           (isinstance(child, Rectangle) and hasattr(child, 'get_zorder') and 
                            child.get_zorder() >= 14)]
            for item in to_remove:
                try: item.remove()
                except: pass
        
        self.add_navigation_buttons()
        self.canvas.draw_idle()

    def add_navigation_buttons(self):
        """네비게이션 버튼 추가 - 코드 중복 제거"""
        button_configs = [
            ('home_1', '⌂', '#2d2d2d'), ('zoom_in_1', '⊕', '#0066cc'), ('zoom_out_1', '⊖', '#0066cc'),
            ('home_2', '⌂', '#2d2d2d'), ('zoom_in_2', '⊕', '#0066cc'), ('zoom_out_2', '⊖', '#0066cc')
        ]
        
        # 툴박스 설정
        button_width, button_height, button_spacing = 0.035, 0.035, 0.005
        padding = 0.008
        toolbox_width = button_width + 2 * padding
        toolbox_height = 3 * button_height + 2 * button_spacing + 2 * padding
        toolbox_x, toolbox_y = 0.99 - toolbox_width, 0.99 - toolbox_height
        
        for i, ax in enumerate([self.ax1, self.ax2]):
            # 툴박스 배경 및 그림자
            shadow_bg = Rectangle((toolbox_x + 0.002, toolbox_y - 0.002), toolbox_width, toolbox_height,
                                facecolor='#d0d0d0', alpha=0.5, transform=ax.transAxes, zorder=14)
            toolbox_bg = Rectangle((toolbox_x, toolbox_y), toolbox_width, toolbox_height,
                                 facecolor='#f0f0f0', edgecolor='#a0a0a0', linewidth=1, 
                                 alpha=1.0, transform=ax.transAxes, zorder=15)
            ax.add_patch(shadow_bg)
            ax.add_patch(toolbox_bg)
            
            # 버튼들
            button_x = toolbox_x + padding
            for j in range(3):
                gid, icon, color = button_configs[i*3 + j]
                button_y = toolbox_y + padding + (2-j) * (button_height + button_spacing)
                
                is_pressed = (self.button_pressed == gid)
                btn_color = '#cce0ff' if is_pressed else '#ffffff'
                border_color = '#808080' if is_pressed else '#c0c0c0'
                
                btn_bg = Rectangle((button_x, button_y), button_width, button_height,
                                 facecolor=btn_color, edgecolor=border_color, linewidth=1,
                                 transform=ax.transAxes, zorder=16)
                ax.add_patch(btn_bg)
                
                if not is_pressed:
                    highlight = Rectangle((button_x, button_y + button_height - 0.002), 
                                        button_width, 0.002, facecolor='white', alpha=0.8,
                                        transform=ax.transAxes, zorder=17)
                    ax.add_patch(highlight)
                
                ax.text(button_x + button_width/2, button_y + button_height/2, icon, 
                       transform=ax.transAxes, fontsize=9, ha='center', va='center', 
                       picker=True, gid=gid, zorder=18, fontweight='bold', color=color)  # 18 → 9
            
            # 사용법 힌트 - 크기 절반으로
            hint_props = {'boxstyle': 'round,pad=0.025', 'facecolor': 'white', 
                         'alpha': 0.8, 'edgecolor': '#ccc', 'linewidth': 0.5}  # pad 절반
            ax.text(0.02, 0.02, 'Wheel:Zoom | Click+Drag:Pan', transform=ax.transAxes, 
                   fontsize=2.5, ha='left', va='bottom', bbox=hint_props, zorder=20, color='#666')  # 폰트 크기 절반

    def update_plot(self):
        """최적화된 플롯 업데이트"""
        # 축 범위 보존
        prev_limits = None
        if self.preserve_axis_limits and hasattr(self.ax1, 'get_xlim'):
            prev_limits = (self.ax1.get_xlim(), self.ax1.get_ylim(), 
                          self.ax2.get_xlim(), self.ax2.get_ylim())
        
        # 좌표 텍스트 초기화
        self.coord_text1 = None
        self.coord_text2 = None
        
        self.ax1.clear(); self.ax2.clear()
        
        # 배경 및 경계선
        if self.show_bg:
            alpha = self.bg_alpha/100
            if self.cie1931_bg is not None: 
                self.ax1.imshow(self.cie1931_bg, extent=[0,0.8,0,0.9], aspect='auto', alpha=alpha, zorder=0)
            if self.cie1976_bg is not None: 
                self.ax2.imshow(self.cie1976_bg, extent=[0,0.7,0,0.6], aspect='auto', alpha=alpha, zorder=0)
        
        if self.show_boundaries:
            spectral_x, spectral_y = calculate_spectral_locus()
            if len(spectral_x) > 0:
                # CIE 1931 경계선
                self.ax1.plot(spectral_x, spectral_y, 'k-', linewidth=1.5, alpha=0.7, zorder=2)
                self.ax1.plot([spectral_x[-1], spectral_x[0]], [spectral_y[-1], spectral_y[0]], 
                             'k-', linewidth=1.5, alpha=0.7, zorder=2)
                
                # CIE 1976 경계선
                u_vals, v_vals = xy_to_uv_vectorized(spectral_x, spectral_y)
                valid_mask = ~(np.isnan(u_vals) | np.isnan(v_vals))
                if np.any(valid_mask):
                    u_clean, v_clean = u_vals[valid_mask], v_vals[valid_mask]
                    self.ax2.plot(u_clean, v_clean, 'k-', linewidth=1.5, alpha=0.7, zorder=2)
                    self.ax2.plot([u_clean[-1], u_clean[0]], [v_clean[-1], v_clean[0]], 
                                 'k-', linewidth=1.5, alpha=0.7, zorder=2)
        
        # Blackbody locus 표시
        selected_intervals = [interval for interval, checked in self.blackbody_intervals.items() if checked]
        
        if selected_intervals:
            bb_x, bb_y, bb_u, bb_v, bb_temps = calculate_blackbody_locus()
            
            if len(bb_x) > 0:
                # 현재 축 범위 가져오기
                x_range = self.ax1.get_xlim()
                y_range = self.ax1.get_ylim()
                u_range = self.ax2.get_xlim()
                v_range = self.ax2.get_ylim()
                
                # CIE 1931 blackbody locus - 검은색으로 두드러지게
                self.ax1.plot(bb_x, bb_y, color='black', linewidth=2.0, alpha=0.8, 
                             linestyle='-', zorder=2)
                
                # CIE 1976 blackbody locus - 검은색으로 두드러지게
                self.ax2.plot(bb_u, bb_v, color='black', linewidth=2.0, alpha=0.8, 
                             linestyle='-', zorder=2)
                
                # 각 선택된 간격별로 DUV 라인 그리기
                for interval in selected_intervals:
                    # 범위에 따른 DUV 라인 생성 (선택된 간격 사용)
                    label_data, duv_lines_1931, duv_lines_1976 = get_duv_lines_for_range(
                        x_range, y_range, u_range, v_range, interval)
                    
                    # Duv 라인 표시 (등상관색온도선) - 회색으로 은은하게
                    for x1, y1, x2, y2 in duv_lines_1931:
                        self.ax1.plot([x1, x2], [y1, y2], color='gray', 
                                     linewidth=1.5, alpha=0.7, zorder=2)
                    
                    for u1, v1, u2, v2 in duv_lines_1976:
                        self.ax2.plot([u1, u2], [v1, v2], color='gray', 
                                     linewidth=1.5, alpha=0.7, zorder=2)
                    
                    # 온도 라벨 표시 (박스 없이 글자만) - 간격별로 다른 색상으로?
                    for label_info in label_data:
                        temp = label_info['temp']
                        # CIE 1931 라벨
                        self.ax1.text(label_info['x'], label_info['y'], f"{temp}K", 
                                     fontsize=8, ha='center', va='center', 
                                     color='black', alpha=0.8, zorder=3, fontweight='bold')
                        
                        # CIE 1976 라벨
                        self.ax2.text(label_info['u'], label_info['v'], f"{temp}K", 
                                     fontsize=8, ha='center', va='center', 
                                     color='black', alpha=0.8, zorder=3, fontweight='bold')
        
        # 데이터 플롯
        sel = [a for a, v in self.angle_vars.items() if v]
        if csv_loaded and sel:
            bounds1 = [np.inf, -np.inf, np.inf, -np.inf]
            bounds2 = [np.inf, -np.inf, np.inf, -np.inf]
            meds1, meds2 = [], []
            scatter_handles, scatter_labels = [], []
            shift_handles, shift_labels = [], []
            
            # 각 angle별 데이터 처리
            for a in sel:
                color = COLORS[ANGLES.index(a)]
                xs, ys = data[f"{a}_x"].values, data[f"{a}_y"].values
                gm = geometric_median(np.c_[xs, ys])
                meds1.append(gm)
                meds2.append(xy_to_uv(*gm))
                
                # 산점도
                self.ax1.scatter(xs, ys, color=color, s=25, alpha=0.3, zorder=5, edgecolors='none')
                
                # CIE 1976 변환 및 플롯
                u_vals, v_vals = xy_to_uv_vectorized(xs, ys)
                valid_mask = ~(np.isnan(u_vals) | np.isnan(v_vals))
                if np.any(valid_mask):
                    self.ax2.scatter(u_vals[valid_mask], v_vals[valid_mask], 
                                   color=color, s=25, alpha=0.3, zorder=5, edgecolors='none')
                
                # 경계 업데이트
                bounds1[0] = min(bounds1[0], xs.min()); bounds1[1] = max(bounds1[1], xs.max())
                bounds1[2] = min(bounds1[2], ys.min()); bounds1[3] = max(bounds1[3], ys.max())
                if np.any(valid_mask):
                    u_clean, v_clean = u_vals[valid_mask], v_vals[valid_mask]
                    bounds2[0] = min(bounds2[0], u_clean.min()); bounds2[1] = max(bounds2[1], u_clean.max())
                    bounds2[2] = min(bounds2[2], v_clean.min()); bounds2[3] = max(bounds2[3], v_clean.max())
            
            # 기하중앙값 표시
            for i, gm in enumerate(meds1):
                color = COLORS[ANGLES.index(sel[i])]
                angle_text = f" {sel[i]}°" if sel[i] < 10 else f"{sel[i]}°"
                m1 = self.ax1.scatter(*gm, s=200, edgecolors=color, facecolors='none', 
                                    lw=3, alpha=0.8, zorder=8, label=f'{angle_text} median')
                self.ax2.scatter(*meds2[i], s=200, edgecolors=color, facecolors='none', 
                               lw=3, alpha=0.8, zorder=8)
                scatter_handles.append(m1)
                scatter_labels.append(f'{angle_text} median')
            
            # 화살표 및 전환 정보
            for i in range(len(meds1)-1):
                x1, y1, x2, y2 = *meds1[i], *meds1[i+1]
                u1, v1, u2, v2 = *meds2[i], *meds2[i+1]
                arrow_color = TRANSITION_COLORS[i % len(TRANSITION_COLORS)]
                
                # 거리 계산
                d1, d2 = np.hypot(x2-x1, y2-y1), np.hypot(u2-u1, v2-v1)
                Lab1, Lab2 = XYZ_to_Lab(*xy_to_XYZ(x1, y1)), XYZ_to_Lab(*xy_to_XYZ(x2, y2))
                dE = deltaE2000(Lab1, Lab2)
                
                # 화살표
                props = {'arrowstyle': '-|>', 'mutation_scale': 25, 'lw': 5, 
                        'color': arrow_color, 'alpha': 0.8}
                self.ax1.annotate('', xy=(x2, y2), xytext=(x1, y1), arrowprops=props, zorder=10)
                self.ax2.annotate('', xy=(u2, v2), xytext=(u1, v1), arrowprops=props, zorder=10)
                
                # 범례 정보
                start_text = f" {sel[i]}°" if sel[i] < 10 else f"{sel[i]}°"
                end_text = f" {sel[i+1]}°" if sel[i+1] < 10 else f"{sel[i+1]}°"
                label = f'{start_text} → {end_text}, Δxy={d1:.3f}, Δuv={d2:.3f}, ΔE00={dE:.2f}'
                line1 = self.ax1.plot([], [], color=arrow_color, linewidth=5, alpha=0.8, label=label)[0]
                shift_handles.append(line1)
                shift_labels.append(label)
            
            # 색상 변화 박스
            if len(sel) >= 3:
                total_dE = sum(deltaE2000(XYZ_to_Lab(*xy_to_XYZ(*meds1[i])), 
                                        XYZ_to_Lab(*xy_to_XYZ(*meds1[i+1]))) 
                             for i in range(len(meds1)-1))
                
                for ax in [self.ax1, self.ax2]:
                    xlim, ylim = ax.get_xlim(), ax.get_ylim()
                    box_x = xlim[0] + (xlim[1] - xlim[0]) * 0.4
                    box_y = ylim[0] + (ylim[1] - ylim[0]) * 0.5
                    box_w, box_h = (xlim[1] - xlim[0]) * 0.12, (ylim[1] - ylim[0]) * 0.09  # 박스 크기 절반
                    
                    color_box = Rectangle((box_x, box_y), box_w, box_h, 
                                        facecolor='lightblue', edgecolor='navy', 
                                        linewidth=2, alpha=0.8, zorder=12)
                    ax.add_patch(color_box)
                    ax.text(box_x + box_w/2, box_y + box_h/2, f'Total ΔE00:\n{total_dE:.2f}', 
                           fontsize=7, ha='center', va='center', fontweight='bold', zorder=13)  # 폰트 크기 절반
                
                box_handle = Rectangle((0, 0), 1, 1, facecolor='lightblue', 
                                     edgecolor='navy', linewidth=2, alpha=0.8)
                shift_handles.append(box_handle)
                shift_labels.append(f'Total Color Shift (ΔE00={total_dE:.2f})')
            
            # 범례 생성 - 크기 절반으로
            for ax, title_suffix in [(self.ax1, ''), (self.ax2, '_2')]:
                if scatter_handles:
                    legend1 = ax.legend(scatter_handles, scatter_labels, loc='upper left', 
                                      framealpha=0.95, fancybox=True, shadow=True, title='Median Points')
                    legend1.get_title().set_fontsize(9)  # 18 → 9
                    legend1.get_title().set_fontweight('bold')
                
                if shift_handles:
                    legend2 = ax.legend(shift_handles, shift_labels, loc='lower right', 
                                      framealpha=0.95, fancybox=True, shadow=True, title='Color Shifts')
                    legend2.get_title().set_fontsize(9)  # 18 → 9
                    legend2.get_title().set_fontweight('bold')
                    if scatter_handles: ax.add_artist(legend1)
            
            # 축 범위 설정
            self._set_axis_limits(bounds1, bounds2, prev_limits)
        else:
            # 데이터 없을 때 축 범위 설정
            self._set_default_limits(prev_limits)
        
        # 레이블, 그리드, 타이틀
        self.ax1.set_xlabel('CIE x'); self.ax1.set_ylabel('CIE y'); self.ax1.grid(True, ls='--', alpha=0.5)
        self.ax2.set_xlabel("CIE u'"); self.ax2.set_ylabel("CIE v'"); self.ax2.grid(True, ls='--', alpha=0.5)
        
        # 제목 - 크기와 박스 절반으로
        title_props = {'fontsize': 12, 'fontweight': 'bold', 'ha': 'center', 'va': 'top',
                      'bbox': dict(boxstyle='round,pad=0.15', facecolor='white', alpha=0.8), 'zorder': 19}  # pad 절반
        self.ax1.text(0.5, 0.98, 'CIE 1931', transform=self.ax1.transAxes, **title_props)
        self.ax2.text(0.5, 0.98, 'CIE 1976', transform=self.ax2.transAxes, **title_props)
        
        # 네비게이션 버튼 및 마무리
        self.add_navigation_buttons()
        if self.preserve_axis_limits: self.save_axis_limits()
        self.canvas.draw()

    def _set_axis_limits(self, bounds1, bounds2, prev_limits):
        """축 범위 설정 로직 분리"""
        if self.preserve_axis_limits and self.ax1_xlim is not None:
            self.ax1.set_xlim(self.ax1_xlim); self.ax1.set_ylim(self.ax1_ylim)
            self.ax2.set_xlim(self.ax2_xlim); self.ax2.set_ylim(self.ax2_ylim)
        elif self.preserve_axis_limits and prev_limits:
            self.ax1.set_xlim(prev_limits[0]); self.ax1.set_ylim(prev_limits[1])
            self.ax2.set_xlim(prev_limits[2]); self.ax2.set_ylim(prev_limits[3])
        else:
            m = 0.1
            xmn, xmx, ymn, ymx = bounds1
            self.ax1.set_xlim(max(0, xmn-(xmx-xmn)*m), min(0.8, xmx+(xmx-xmn)*m))
            self.ax1.set_ylim(max(0, ymn-(ymx-ymn)*m), min(0.9, ymx+(ymx-ymn)*m))
            
            umn, umx, vmn, vmx = bounds2
            self.ax2.set_xlim(max(0, umn-(umx-umn)*m), min(0.7, umx+(umx-umn)*m))
            self.ax2.set_ylim(max(0, vmn-(vmx-vmn)*m), min(0.6, vmx+(vmx-vmn)*m))

    def _set_default_limits(self, prev_limits):
        """기본 축 범위 설정"""
        if self.preserve_axis_limits and self.ax1_xlim is not None:
            self.ax1.set_xlim(self.ax1_xlim); self.ax1.set_ylim(self.ax1_ylim)
            self.ax2.set_xlim(self.ax2_xlim); self.ax2.set_ylim(self.ax2_ylim)
        elif self.preserve_axis_limits and prev_limits:
            self.ax1.set_xlim(prev_limits[0]); self.ax1.set_ylim(prev_limits[1])
            self.ax2.set_xlim(prev_limits[2]); self.ax2.set_ylim(prev_limits[3])
        elif self.show_bg or self.show_boundaries:
            self.ax1.set_xlim(0, 0.8); self.ax1.set_ylim(0, 0.9)
            self.ax2.set_xlim(0, 0.7); self.ax2.set_ylim(0, 0.6)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fig.set_size_inches(self.canvas.width()/100, self.canvas.height()/100)
        self.canvas.draw()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())