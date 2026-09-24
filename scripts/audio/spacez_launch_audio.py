# -*- coding: utf-8 -*-
"""Space-Z 발사 사운드 — 카운트다운 음성(관제 무선 톤) + 발사 추진음(점화→최대추력→이탈).
출력: public/assets/sfx/spacez/*.mp3  (재생성 가능 — 이 스크립트가 원본)"""
import numpy as np, subprocess, os
from scipy.io import wavfile
from scipy.signal import butter, sosfilt, fftconvolve

SR = 44100
HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'spacez_voice')  # SAPI Zira 원본 (PowerShell System.Speech 로 생성)
OUT = 'C:/code/python/luckyplz/public/assets/sfx/spacez'
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(20260924)

def bp(x, lo, hi, order=4):
    return sosfilt(butter(order, [lo, hi], btype='band', fs=SR, output='sos'), x)
def lp(x, f, order=4):
    return sosfilt(butter(order, f, btype='low', fs=SR, output='sos'), x)
def hp(x, f, order=4):
    return sosfilt(butter(order, f, btype='high', fs=SR, output='sos'), x)

def load(name):
    sr, x = wavfile.read(os.path.join(HERE, name))
    assert sr == SR
    x = x.astype(np.float64) / 32768.0
    # 앞뒤 무음 제거
    env = np.abs(x) > 0.01
    idx = np.where(env)[0]
    x = x[max(0, idx[0] - 200): idx[-1] + 2200]
    return x / (np.max(np.abs(x)) + 1e-9)

def quindar(f, dur=0.13):
    t = np.arange(int(dur * SR)) / SR
    s = np.sin(2 * np.pi * f * t) * 0.32
    fade = int(0.006 * SR)
    s[:fade] *= np.linspace(0, 1, fade); s[-fade:] *= np.linspace(1, 0, fade)
    return s

def radio(x):
    """관제 무선: 대역 제한 + 소프트 클립 + 얇은 잡음 바닥 + 짧은 방 울림"""
    y = hp(x, 320); y = lp(y, 3500)
    y = np.tanh(y * 2.6) / np.tanh(2.6)
    hiss = bp(rng.standard_normal(len(y)), 900, 5000) * 0.018
    y = y + hiss
    ir = np.zeros(int(0.09 * SR)); ir[0] = 1.0
    ir[int(0.021 * SR)] = 0.22; ir[int(0.047 * SR)] = 0.12
    y = fftconvolve(y, ir)[:len(y)]
    fade = int(0.01 * SR)
    y[:fade] *= np.linspace(0, 1, fade); y[-fade * 3:] *= np.linspace(1, 0, fade * 3)
    return y / (np.max(np.abs(y)) + 1e-9) * 0.9

def enc(name, y, br='96k'):
    y = np.clip(y, -1, 1)
    tmp = os.path.join(HERE, name + '.tmp.wav')
    wavfile.write(tmp, SR, (y * 32767).astype(np.int16))
    subprocess.run(['C:/ffmpeg/bin/ffmpeg', '-y', '-loglevel', 'error', '-i', tmp,
                    '-ac', '1', '-ar', '44100', '-b:a', br, os.path.join(OUT, name + '.mp3')], check=True)
    os.remove(tmp)
    print(name, round(len(y) / SR, 2), 's', os.path.getsize(os.path.join(OUT, name + '.mp3')), 'bytes')

# ── 음성 ──
gap = np.zeros(int(0.03 * SR))
three = np.concatenate([quindar(2525), gap, radio(load('v_three.wav'))])  # 송신 시작 Quindar 톤
enc('cd-3', three, '64k')
enc('cd-2', radio(load('v_two.wav')), '64k')
enc('cd-1', radio(load('v_one.wav')), '64k')
launch = radio(load('v_launch.wav'))
enc('cd-launch', np.concatenate([launch, np.zeros(int(0.12 * SR)), quindar(2475, 0.2)]), '64k')

# ── 발사 추진음 ──
# 타임라인: 0.0 점화(카운트 "1") → 0.9 최대추력(LAUNCH) → 3.4 부터 로켓이 멀어지며 감쇠 → 10s
D = 10.0
n = int(D * SR); t = np.arange(n) / SR
thrust = np.clip(t / 0.9, 0, 1) ** 1.6                                  # 점화에서 최대까지
thrust *= np.where(t < 3.4, 1.0, np.exp(-(t - 3.4) / 2.3))              # 이탈 감쇠
far = np.clip((t - 3.0) / 6.0, 0, 1)                                    # 멀어질수록 고역이 먼저 사라진다

w = rng.standard_normal(n)
brown = np.cumsum(rng.standard_normal(n)); brown -= lp(brown, 3); brown /= np.max(np.abs(brown))
rumble = lp(brown, 140) * 2.2                                            # 땅울림
am = 0.75 + 0.25 * lp(rng.standard_normal(n), 3) / 0.05                  # 느린 요동
am = np.clip(am, 0.4, 1.3)
body = bp(w, 140, 900) * am                                              # 포효 몸통
air = bp(w, 900, 5200) * am * (1 - 0.85 * far)                           # 쉬익 — 멀어지며 사라짐

# 크래클 — 초음속 배기의 "딱딱" 터지는 소리. 추력에 비례해 밀도↑, 두꺼운 꼬리 분포 진폭
crk = np.zeros(n)
rate = 520
k = 0
tt = 0.05
while tt < D:
    tt += rng.exponential(1.0 / (rate * max(0.05, np.interp(tt, t, thrust))))
    i = int(tt * SR)
    if i >= n - 400: break
    L = int(rng.uniform(0.0006, 0.0035) * SR)
    a = min(3.0, rng.pareto(2.2) + 0.3) * np.interp(tt, t, thrust)
    burst = rng.standard_normal(L) * np.exp(-np.arange(L) / (L / 3.5))
    crk[i:i + L] += burst * a
    k += 1
crk = hp(crk, 700) * (1 - 0.9 * far)

sub = (np.sin(2 * np.pi * 33 * t) + 0.6 * np.sin(2 * np.pi * 47 * t + 1.3)) * (0.7 + 0.3 * am)
# 점화 "훙" — 낮은 붐 + 노이즈 한 덩이
boom_t = t[:int(0.9 * SR)]
boom = np.sin(2 * np.pi * (85 * boom_t - 28 * boom_t ** 2)) * np.exp(-boom_t / 0.28)
boom = np.concatenate([boom, np.zeros(n - len(boom))])
bn = lp(w, 400) * np.exp(-t / 0.18) * 0.8

dry = (rumble * 0.45 + body * 2.4 + air * 0.9 + crk * 1.1 + sub * 0.16) * thrust + boom * 0.35 + bn * 0.9
# 야외 발사장 울림: 짧은 지면 반사 + 긴 꼬리
L = int(3.2 * SR)
ir = rng.standard_normal(L) * np.exp(-np.arange(L) / SR / 0.9)
ir = lp(ir, 2500)
ir[0] += 6.0; ir[int(0.31 * SR)] += 1.6; ir[int(0.74 * SR)] += 0.9
wet = fftconvolve(dry, ir)[:n]
wet /= np.max(np.abs(wet)) + 1e-9
y = dry / (np.max(np.abs(dry)) + 1e-9) * 0.55 + wet * 0.6
y = np.tanh(y * 1.8) / np.tanh(1.8)
fo = int(0.8 * SR); y[-fo:] *= np.linspace(1, 0, fo)
y = y / np.max(np.abs(y)) * 0.95
print('crackles', k)
enc('launch-roar', y, '96k')
