# -*- coding: utf-8 -*-
"""Accurate CIE 1931 colorimetry data + helpers for the Color Science series.

Replaces the earlier crude Gaussian approximation. Uses the real CIE 1931 2-deg
standard-observer XYZ color-matching functions (5nm table, Wyszecki & Stiles),
cubic-interpolated to 1nm, and an xy->sRGB conversion to FILL the chromaticity
horseshoe with true colors (the way a proper diagram looks). Adapted from the
user's ColorTrack reference (generate_cie_diagrams_edu.py).

Run locally only (needs numpy + scipy); the generated PNGs are committed static.
"""
import numpy as np
from scipy.interpolate import interp1d

# --- CIE 1931 2-deg standard observer, 380..780nm @ 5nm (81 pts) -----------
WL5 = np.arange(380, 785, 5)

X5 = np.array([
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
    0.000042])

Y5 = np.array([
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
    0.000015])

Z5 = np.array([
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
    0.000000])

# RGB->XYZ matrix for the CIE 1931 RGB system (primaries 700, 546.1, 435.8nm)
_M_RGB2XYZ = np.array([
    [0.49000, 0.31000, 0.20000],
    [0.17697, 0.81240, 0.01063],
    [0.00000, 0.01000, 0.99000]]) / 0.17697
_M_XYZ2RGB = np.linalg.inv(_M_RGB2XYZ)

# linear-sRGB matrix (D65)
_M_XYZ2SRGB = np.array([
    [3.2406, -1.5372, -0.4986],
    [-0.9689, 1.8758, 0.0415],
    [0.0557, -0.2040, 1.0570]])

_cache = {}


def cmf_1nm():
    """Cubic-interpolated XYZ CMF at 1nm (380..780). Cached."""
    if "cmf" not in _cache:
        wl = np.arange(380, 781, 1)
        x = np.maximum(interp1d(WL5, X5, kind="cubic", bounds_error=False, fill_value=0)(wl), 0)
        y = np.maximum(interp1d(WL5, Y5, kind="cubic", bounds_error=False, fill_value=0)(wl), 0)
        z = np.maximum(interp1d(WL5, Z5, kind="cubic", bounds_error=False, fill_value=0)(wl), 0)
        _cache["cmf"] = (wl, x, y, z)
    return _cache["cmf"]


def rgb_cmf():
    """CIE 1931 RGB color-matching functions r̄ ḡ b̄ at 1nm (has the negatives)."""
    wl, x, y, z = cmf_1nm()
    xyz = np.vstack([x, y, z])              # 3 x N
    rgb = _M_XYZ2RGB @ xyz                  # 3 x N
    return wl, rgb[0], rgb[1], rgb[2]


def spectral_locus():
    """(wl, x, y) of the spectral locus at 1nm."""
    wl, X, Y, Z = cmf_1nm()
    s = X + Y + Z
    m = s > 1e-12
    return wl[m], (X[m] / s[m]), (Y[m] / s[m])


def xy_to_uv1976(x, y):
    d = -2 * x + 12 * y + 3
    return 4 * x / d, 9 * y / d


def _xy_to_srgb_grid(xg, yg):
    """Vectorized xy->sRGB (Y=1, max-normalized, gamma). xg,yg are 2D arrays."""
    with np.errstate(divide="ignore", invalid="ignore"):
        Y = np.ones_like(yg)
        X = xg * Y / yg
        Z = (1 - xg - yg) * Y / yg
    XYZ = np.stack([X, Y, Z], axis=-1)                  # H,W,3
    rgb = XYZ @ _M_XYZ2SRGB.T                            # H,W,3
    rgb = np.clip(rgb, 0, None)
    mx = rgb.max(axis=-1, keepdims=True)
    rgb = np.where(mx > 1, rgb / np.where(mx == 0, 1, mx), rgb)
    rgb = np.where(rgb <= 0.0031308, 12.92 * rgb, 1.055 * np.power(np.clip(rgb, 0, None), 1 / 2.4) - 0.055)
    return np.clip(rgb, 0, 1)


def _inside_hull(XG, YG, poly):
    """Vectorized inside-the-convex-hull test via scipy Delaunay (robust)."""
    from scipy.spatial import Delaunay
    tri = Delaunay(poly)
    pts = np.column_stack([XG.ravel(), YG.ravel()])
    return (tri.find_simplex(pts) >= 0).reshape(XG.shape)


def render_chromaticity_png(out_path, mode="1931", res=900, xr=(0, 0.8), yr=(0, 0.9)):
    """Filled chromaticity diagram PNG (gamut only, transparent outside).

    mode '1931' -> xy plane; '1976' -> u'v' plane. Row 0 = top = max-y.
    Returns (xr, yr) actually used so the SVG overlay can align.
    """
    from PIL import Image
    wl, sx, sy = spectral_locus()
    if mode == "1976":
        sx, sy = xy_to_uv1976(sx, sy)
        xr, yr = (0, 0.65), (0, 0.62)
    poly = np.column_stack([sx, sy])

    W = res
    H = int(res * (yr[1] - yr[0]) / (xr[1] - xr[0]))
    jx = np.linspace(xr[0], xr[1], W)
    iy = np.linspace(yr[1], yr[0], H)   # row 0 = top = max y
    XG, YG = np.meshgrid(jx, iy)
    inside = _inside_hull(XG, YG, poly) & (YG > 1e-3)
    if mode == "1976":
        # convert grid back to xy for sRGB
        d = 6 * XG - 16 * YG + 12
        xx = 9 * XG / d
        yy = 4 * YG / d
        rgb = _xy_to_srgb_grid(xx, yy)
    else:
        rgb = _xy_to_srgb_grid(XG, YG)
    rgb = np.nan_to_num(rgb, nan=0.0)
    img = np.zeros((H, W, 4), dtype=np.uint8)
    img[..., :3] = np.clip(rgb * 255, 0, 255).astype(np.uint8)
    img[..., 3] = np.where(inside, 255, 0).astype(np.uint8)
    Image.fromarray(img, "RGBA").save(out_path)
    return xr, yr


# wavelength label anchor points (xy or uv) for the overlay
def locus_label_points(mode="1931"):
    wl, sx, sy = spectral_locus()
    if mode == "1976":
        sx, sy = xy_to_uv1976(sx, sy)
    out = {}
    for w in (460, 480, 490, 500, 510, 520, 540, 560, 580, 600, 620, 700):
        idx = int(np.argmin(np.abs(wl - w)))
        out[w] = (float(sx[idx]), float(sy[idx]))
    return out


def locus_polyline(mode="1931"):
    wl, sx, sy = spectral_locus()
    if mode == "1976":
        sx, sy = xy_to_uv1976(sx, sy)
    return list(zip(sx.tolist(), sy.tolist()))
