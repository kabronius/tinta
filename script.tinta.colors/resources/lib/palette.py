"""Material 3 dark colour scheme from a seed colour.

Model: M3 "tones" are taken as CIE L* (0-100). Each tonal palette has a fixed hue and chroma in
CIE LCh(ab); the colour of a tone is the one at L* = tone, with chroma reduced until it fits the
sRGB gamut. This approximates HCT (which uses CAM16), closely enough for a skin and much lighter.

No Kodi dependency: testable outside Kodi.
"""
import colorsys
import math

# M3 dark scheme tone per role: (palette, tone)
DARK_ROLES = {
    "Primary": ("p", 80), "OnPrimary": ("p", 20),
    "PrimaryContainer": ("p", 30), "OnPrimaryContainer": ("p", 90),
    "Secondary": ("s", 80), "OnSecondary": ("s", 20),
    "SecondaryContainer": ("s", 30), "OnSecondaryContainer": ("s", 90),
    "Tertiary": ("t", 80), "OnTertiary": ("t", 20),
    "TertiaryContainer": ("t", 30), "OnTertiaryContainer": ("t", 90),
    "Surface": ("n", 6), "SurfaceDim": ("n", 6), "SurfaceBright": ("n", 24),
    "SurfaceContainerLowest": ("n", 4), "SurfaceContainerLow": ("n", 10),
    "SurfaceContainer": ("n", 12), "SurfaceContainerHigh": ("n", 17),
    "SurfaceContainerHighest": ("n", 22),
    "OnSurface": ("n", 90), "OnSurfaceVariant": ("nv", 80),
    "Outline": ("nv", 60), "OutlineVariant": ("nv", 30),
    "InverseSurface": ("n", 90), "InverseOnSurface": ("n", 20), "InversePrimary": ("p", 40),
}

DEFAULT_SEED = (0x67, 0x50, 0xA4)  # M3 baseline


# --- colour conversions -------------------------------------------------------
def _srgb_to_linear(c):
    c /= 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _linear_to_srgb(c):
    c = 12.92 * c if c <= 0.0031308 else 1.055 * (c ** (1 / 2.4)) - 0.055
    return c * 255.0


_WHITE = (0.95047, 1.0, 1.08883)


def _f(t):
    return t ** (1 / 3) if t > 216 / 24389 else (24389 / 27 * t + 16) / 116


def _finv(t):
    t3 = t ** 3
    return t3 if t3 > 216 / 24389 else (116 * t - 16) / (24389 / 27)


def rgb_to_lch(rgb):
    r, g, b = (_srgb_to_linear(c) for c in rgb)
    x = 0.4124564 * r + 0.3575761 * g + 0.1804375 * b
    y = 0.2126729 * r + 0.7151522 * g + 0.0721750 * b
    z = 0.0193339 * r + 0.1191920 * g + 0.9503041 * b
    fx, fy, fz = _f(x / _WHITE[0]), _f(y / _WHITE[1]), _f(z / _WHITE[2])
    L = 116 * fy - 16
    a = 500 * (fx - fy)
    bb = 200 * (fy - fz)
    return L, math.hypot(a, bb), math.degrees(math.atan2(bb, a)) % 360


def _lab_to_rgb_unclamped(L, a, b):
    fy = (L + 16) / 116
    fx = fy + a / 500
    fz = fy - b / 200
    x, y, z = _finv(fx) * _WHITE[0], _finv(fy) * _WHITE[1], _finv(fz) * _WHITE[2]
    r = 3.2404542 * x - 1.5371385 * y - 0.4985314 * z
    g = -0.9692660 * x + 1.8760108 * y + 0.0415560 * z
    bl = 0.0556434 * x - 0.2040259 * y + 1.0572252 * z
    return r, g, bl


def tone(hue, chroma, t):
    """sRGB colour (0-255) at tone t, with chroma reduced until it fits the gamut."""
    if t <= 0:
        return (0, 0, 0)
    if t >= 100:
        return (255, 255, 255)
    h = math.radians(hue)

    def in_gamut(c):
        lin = _lab_to_rgb_unclamped(t, c * math.cos(h), c * math.sin(h))
        return lin if all(-1e-4 <= v <= 1.0001 for v in lin) else None

    best = in_gamut(chroma)
    if best is None:  # bisection on the highest in-gamut chroma
        lo, hi = 0.0, chroma
        best = in_gamut(0.0)
        for _ in range(18):
            c = (lo + hi) / 2
            lin = in_gamut(c)
            if lin is None:
                hi = c
            else:
                lo, best = c, lin
    return tuple(int(round(min(255, max(0, _linear_to_srgb(min(1, max(0, v))))))) for v in best)


# --- seed choice ----------------------------------------------------------------
def pick_seed(pixels_with_count):
    """pixels_with_count: list of (count, (r, g, b)). Returns (hue, chroma) of the seed.

    Like Material's "Score": favours high chroma with a non-negligible population.
    """
    total = sum(c for c, _ in pixels_with_count) or 1
    best, best_score = None, -1.0
    fallback, fallback_count = None, -1
    for count, rgb in pixels_with_count:
        share = count / total
        L, C, H = rgb_to_lch(rgb)
        if count > fallback_count:
            fallback, fallback_count = (H, C), count
        if share < 0.01 or C < 12 or L < 8 or L > 96:
            continue
        score = (C / 100.0) * 0.7 + min(share * 4, 1.0) * 0.3
        if score > best_score:
            best, best_score = (H, C), score
    if best is None:
        # almost grey image: hue of the largest cluster, low chroma
        if fallback is None:
            _, c, h = rgb_to_lch(DEFAULT_SEED)
        else:
            h, c = fallback
        return h, min(c, 16)
    return best


def scheme_from_seed(hue, chroma):
    pc = max(32.0, min(chroma, 56.0))
    palettes = {
        "p": (hue, pc),
        "s": (hue, pc / 3.0),
        "t": ((hue + 60.0) % 360, pc / 2.0),
        "n": (hue, 5.0),
        "nv": (hue, 9.0),
    }
    out = {}
    for role, (pal, t) in DARK_ROLES.items():
        h, c = palettes[pal]
        out[role] = tone(h, c, t)
    return out


def default_scheme():
    L, C, H = rgb_to_lch(DEFAULT_SEED)
    return scheme_from_seed(H, C)


def to_argb(rgb, alpha=255):
    return "%02X%02X%02X%02X" % (alpha, rgb[0], rgb[1], rgb[2])


def mix(a, b, t):
    return tuple(int(round(x + (y - x) * t)) for x, y in zip(a, b))


def hsl_debug(rgb):
    h, l, s = colorsys.rgb_to_hls(*(c / 255 for c in rgb))
    return round(h * 360), round(s * 100), round(l * 100)
