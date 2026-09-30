"""Text/graphic overlays drawn with Pillow and animated per frame.

No text is ever generated inside the video model; everything readable is
composited here so spelling is exact and the look stays consistent across episodes.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1920
# Clear of the UI that Shorts / TikTok / Reels draw over the frame (top bar, caption
# block, right-hand action buttons). Overlays should stay inside this box.
SAFE = (70, 230, 1010, 1480)
FONT_PATH = Path(__file__).resolve().parents[1] / "fonts" / "LilitaOne-Regular.ttf"

INK = "#2B1A10"          # warm near-black used for outlines
CREAM = "#FFF1D0"
BURNT = "#C4622D"


def font(size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(str(FONT_PATH), size)
    except OSError:
        return ImageFont.truetype("DejaVuSans-Bold.ttf", size)


def rgba(h: str, a: int = 255) -> tuple[int, int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a


# ------------------------------------------------------------------- text layout

def _wrap(draw: ImageDraw.ImageDraw, text: str, fnt, max_w: float) -> list[str]:
    lines: list[str] = []
    for para in text.split("\n"):
        cur = ""
        for w in para.split():
            trial = (cur + " " + w).strip()
            if cur and draw.textlength(trial, font=fnt) > max_w:
                lines.append(cur)
                cur = w
            else:
                cur = trial
        lines.append(cur)
    return lines


def text_layer(text: str, size: int = 90, max_w: int = 900, fill: str = "#FFFFFF",
               stroke_w: int = 9, stroke_fill: str = INK, align: str = "center",
               shadow: tuple | None = (0, 7, 8, 0.45), line_gap: float = 0.06,
               min_size: int = 32, max_lines: int = 4) -> Image.Image:
    """Outlined, shadowed text on a transparent tight canvas. Shrinks to fit."""
    probe = ImageDraw.Draw(Image.new("RGBA", (8, 8)))
    while True:
        fnt = font(size)
        lines = _wrap(probe, text, fnt, max_w - 2 * stroke_w)
        widths = [probe.textlength(s, font=fnt) for s in lines]
        if (max(widths) <= max_w - 2 * stroke_w and len(lines) <= max_lines) or size <= min_size:
            break
        size -= 2
    asc, desc = fnt.getmetrics()
    lh = int((asc + desc) * (1 + line_gap))
    blur = shadow[2] if shadow else 0
    pad = stroke_w + int(blur * 2) + (abs(shadow[1]) if shadow else 0) + 6
    wbox = int(max(widths)) + 2 * pad
    hbox = lh * len(lines) + 2 * pad

    def draw_all(d, color, stroke_color, dx=0, dy=0):
        for i, (s, w) in enumerate(zip(lines, widths)):
            x = pad + (max(widths) - w) / 2 if align == "center" else pad
            d.text((x + dx, pad + i * lh + dy), s, font=fnt, fill=color,
                   stroke_width=stroke_w, stroke_fill=stroke_color)

    img = Image.new("RGBA", (wbox, hbox), (0, 0, 0, 0))
    if shadow:
        sh = Image.new("RGBA", (wbox, hbox), (0, 0, 0, 0))
        draw_all(ImageDraw.Draw(sh), (0, 0, 0, 255), (0, 0, 0, 255), shadow[0], shadow[1])
        sh = sh.filter(ImageFilter.GaussianBlur(shadow[2]))
        sh.putalpha(sh.getchannel("A").point(lambda v: int(v * shadow[3])))
        img = Image.alpha_composite(img, sh)
    draw_all(ImageDraw.Draw(img), rgba(fill), rgba(stroke_fill))
    return img


def _drop_shadow(img: Image.Image, dy: int = 10, blur: int = 12, opacity: float = 0.35) -> Image.Image:
    pad = blur * 3 + dy
    out = Image.new("RGBA", (img.width + 2 * pad, img.height + 2 * pad), (0, 0, 0, 0))
    sh = Image.new("RGBA", out.size, (0, 0, 0, 0))
    sh.paste((0, 0, 0, 255), (pad, pad + dy), img.getchannel("A"))
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    sh.putalpha(sh.getchannel("A").point(lambda v: int(v * opacity)))
    out = Image.alpha_composite(out, sh)
    out.alpha_composite(img, (pad, pad))
    return out


def _spaced(draw, xy, text, fnt, fill, tracking):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += draw.textlength(ch, font=fnt) + tracking


def _spaced_width(draw, text, fnt, tracking):
    return sum(draw.textlength(ch, font=fnt) + tracking for ch in text) - tracking


def _dashed_rect(d: ImageDraw.ImageDraw, box, dash=24, gap=14, width=5, fill=BURNT):
    x0, y0, x1, y1 = box
    x = x0
    while x < x1:
        d.line([(x, y0), (min(x + dash, x1), y0)], fill=rgba(fill), width=width)
        d.line([(x, y1), (min(x + dash, x1), y1)], fill=rgba(fill), width=width)
        x += dash + gap
    y = y0
    while y < y1:
        d.line([(x0, y), (x0, min(y + dash, y1))], fill=rgba(fill), width=width)
        d.line([(x1, y), (x1, min(y + dash, y1))], fill=rgba(fill), width=width)
        y += dash + gap


# --------------------------------------------------------------- overlay kinds

def tag_layer(lines: list[str], rot: float = -4.0) -> Image.Image:
    """Little paper fee-tag: small caption line + big value line."""
    top, big = (lines + [""])[:2]
    f_top, f_big = font(50), font(132)
    probe = ImageDraw.Draw(Image.new("RGBA", (8, 8)))
    w_top = _spaced_width(probe, top, f_top, 6)
    w_big = probe.textlength(big, font=f_big)
    w = int(max(w_top, w_big)) + 150
    h = 330
    card = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=34, fill=rgba(CREAM), outline=rgba(INK), width=6)
    _dashed_rect(d, (26, 26, w - 27, h - 27))
    _spaced(d, ((w - w_top) / 2, 46), top, f_top, rgba("#7A3B16"), 6)
    d.text(((w - w_big) / 2, 118), big, font=f_big, fill=rgba("#D2491F"), stroke_width=3,
           stroke_fill=rgba("#D2491F"))
    card = _drop_shadow(card.rotate(rot, resample=Image.BICUBIC, expand=True))
    return card


def stamp_layer(text: str, color: str = "#CF3A2E", rot: float = -6.0, size: int = 92,
                seed: int = 3) -> Image.Image:
    """Rubber-stamp look: double border, slight ink dropout."""
    fnt = font(size)
    probe = ImageDraw.Draw(Image.new("RGBA", (8, 8)))
    lines = text.split("\n")
    lw = [probe.textlength(s, font=fnt) for s in lines]
    asc, desc = fnt.getmetrics()
    lh = int((asc + desc) * 1.02)
    pad = 44
    w, h = int(max(lw)) + 2 * pad, lh * len(lines) + 2 * pad
    col = rgba(color)
    paper = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(paper).rounded_rectangle((0, 0, w - 1, h - 1), radius=22, fill=rgba(CREAM, 240))
    ink = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(ink)
    d.rounded_rectangle((3, 3, w - 4, h - 4), radius=20, outline=col, width=9)
    d.rounded_rectangle((21, 21, w - 22, h - 22), radius=12, outline=col, width=4)
    for i, (s, ww) in enumerate(zip(lines, lw)):
        d.text(((w - ww) / 2, pad + i * lh - 4), s, font=fnt, fill=col)
    rng = np.random.default_rng(seed)                       # slight ink dropout on the ink only
    speck = np.asarray(Image.fromarray((rng.random((h, w)) * 255).astype("uint8")).filter(ImageFilter.GaussianBlur(1.6)),
                       dtype=np.float32) / 255
    keep = np.clip((speck - 0.36) * 9, 0, 1) * 0.35 + 0.65
    ink.putalpha(Image.fromarray((np.asarray(ink.getchannel("A"), dtype=np.float32) * keep).astype("uint8")))
    layer = Image.alpha_composite(paper, ink)
    return _drop_shadow(layer.rotate(rot, resample=Image.BICUBIC, expand=True), dy=6, blur=8, opacity=0.25)


def check_layer(text: str, icon: str = "check", size: int = 64) -> Image.Image:
    """Checklist row: round green tick or red cross + label on a cream card."""
    fnt = font(size)
    probe = ImageDraw.Draw(Image.new("RGBA", (8, 8)))
    tw = probe.textlength(text, font=fnt)
    asc, desc = fnt.getmetrics()
    h = int(asc + desc) + 56
    r = h // 2 - 14
    w = int(tw) + 2 * r + 120
    card = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=h // 2, fill=rgba(CREAM), outline=rgba(INK), width=5)
    cx, cy = 26 + r, h // 2
    color = "#2E9E5B" if icon == "check" else "#D64545"
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=rgba(color))
    k = r * 0.5
    if icon == "check":
        d.line([(cx - k, cy + 1), (cx - k * 0.25, cy + k * 0.75), (cx + k * 0.95, cy - k * 0.7)],
               fill=rgba("#FFFFFF"), width=max(8, r // 3), joint="curve")
    else:
        d.line([(cx - k * 0.8, cy - k * 0.8), (cx + k * 0.8, cy + k * 0.8)], fill=rgba("#FFFFFF"), width=max(8, r // 3))
        d.line([(cx - k * 0.8, cy + k * 0.8), (cx + k * 0.8, cy - k * 0.8)], fill=rgba("#FFFFFF"), width=max(8, r // 3))
    d.text((26 + 2 * r + 26, (h - (asc + desc)) / 2 - 2), text, font=fnt, fill=rgba("#3A2416"))
    return _drop_shadow(card, dy=8, blur=10, opacity=0.3)


def render(spec: dict, characters: dict | None = None) -> Image.Image:
    kind = spec.get("kind", "text")
    if kind == "tag":
        return tag_layer(spec["lines"], spec.get("rot", -4.0))
    if kind == "stamp":
        return stamp_layer(spec["text"], spec.get("color", "#CF3A2E"), spec.get("rot", -6.0), spec.get("size", 92))
    if kind == "checkitem":
        return check_layer(spec["text"], spec.get("icon", "check"), spec.get("size", 64))
    style = spec.get("style", "hook")
    who = (characters or {}).get(spec.get("who", ""), {})
    presets = {
        "hook": dict(size=92, max_w=900, stroke_w=9),
        "label": dict(size=70, max_w=860, stroke_w=8),
        "subtitle": dict(size=58, max_w=820, stroke_w=7, shadow=(0, 5, 6, 0.5)),
        "cover": dict(size=150, max_w=940, stroke_w=16, shadow=(0, 10, 12, 0.5), max_lines=3),
        "watermark": dict(size=64, max_w=1000, stroke_w=5, fill="#FFEB3B"),
        # lettering for a physical sign in the footage (pair with `rot`, `scale`, `pos`)
        "sign": dict(size=170, max_w=900, stroke_w=0, fill="#D32F2F", shadow=None),
    }[style]
    args = dict(presets)
    args["fill"] = spec.get("fill", who.get("color", args.get("fill", "#FFFFFF")))
    args["stroke_fill"] = spec.get("stroke", who.get("outline", INK))
    return text_layer(spec["text"], **args)


# ------------------------------------------------------------------ animation

def ease_out_back(k: float) -> float:
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (k - 1) ** 3 + c1 * (k - 1) ** 2


DEFAULT_ANIM = {"text": "pop", "tag": "slam", "stamp": "slam", "checkitem": "pop"}
DEFAULT_POS = {"hook": (540, 470), "label": (540, 470), "subtitle": (540, 1300), "cover": (540, 470),
               "watermark": (540, 960), "tag": (540, 1010), "stamp": (540, 1010), "checkitem": (540, 520)}


class Overlay:
    def __init__(self, spec: dict, start: float, end: float, characters: dict | None = None):
        self.spec, self.start, self.end = spec, start, end
        self.img = render(spec, characters)
        kind = spec.get("kind", "text")
        if kind == "text" and spec.get("rot"):
            self.img = self.img.rotate(spec["rot"], resample=Image.BICUBIC, expand=True)
        if spec.get("scale", 1.0) != 1.0:
            s = spec["scale"]
            self.img = self.img.resize((max(1, round(self.img.width * s)), max(1, round(self.img.height * s))), Image.LANCZOS)
        key = spec.get("style", "hook") if kind == "text" else kind
        self.cx, self.cy = spec.get("pos", DEFAULT_POS.get(key, (540, 470)))
        self.anim = spec.get("anim", DEFAULT_ANIM.get(kind, "pop"))
        if key == "subtitle":
            self.anim = spec.get("anim", "fade")
        self._static = np.asarray(self.img)
        # visible ink only (ignores transparent shadow padding) for safe-zone / collision checks
        self._ink = self.img.getchannel("A").point(lambda v: 255 if v > 48 else 0).getbbox() or (0, 0, *self.img.size)

    def bbox(self) -> tuple[int, int, int, int]:
        w, h = self.img.size
        x, y = self.cx - w / 2, self.cy - h / 2
        return int(x + self._ink[0]), int(y + self._ink[1]), int(x + self._ink[2]), int(y + self._ink[3])

    def outside_safe(self) -> bool:
        x0, y0, x1, y1 = self.bbox()
        return x0 < SAFE[0] or x1 > SAFE[2] or y0 < SAFE[1] or y1 > SAFE[3]

    def active(self, t: float) -> bool:
        return self.start <= t < self.end

    def at(self, t: float):
        """(rgba uint8 array, x, y, alpha multiplier) for time t, or None if not visible."""
        if not self.active(t):
            return None
        u, v = t - self.start, self.end - t
        s, a, dx, dy = 1.0, 1.0, 0.0, 0.0
        if self.anim == "pop":
            s = 0.6 + 0.4 * ease_out_back(min(1.0, u / 0.24))
            a = min(1.0, u / 0.09)
        elif self.anim == "slam":
            k = min(1.0, u / 0.11)
            s = 1.0 + 0.7 * (1 - k) ** 2
            a = min(1.0, u / 0.04)
            if 0.11 < u < 0.30:
                amp = 7 * (1 - (u - 0.11) / 0.19)
                dx, dy = amp * math.sin(u * 90), amp * math.cos(u * 70)
        elif self.anim == "fade":
            a = min(1.0, u / 0.18)
        a *= min(1.0, v / 0.15)
        if abs(s - 1.0) < 1e-3:
            arr = self._static
        else:
            w, h = self.img.size
            arr = np.asarray(self.img.resize((max(1, int(w * s)), max(1, int(h * s))), Image.BICUBIC))
        h, w = arr.shape[:2]
        return arr, int(self.cx + dx - w / 2), int(self.cy + dy - h / 2), a


def blend(frame: np.ndarray, rgba_arr: np.ndarray, x: int, y: int, alpha: float = 1.0) -> None:
    """Alpha-composite rgba_arr onto frame (uint8 HxWx3) in place, clipped to the frame."""
    h, w = rgba_arr.shape[:2]
    fx0, fy0 = max(0, x), max(0, y)
    fx1, fy1 = min(frame.shape[1], x + w), min(frame.shape[0], y + h)
    if fx1 <= fx0 or fy1 <= fy0:
        return
    src = rgba_arr[fy0 - y:fy1 - y, fx0 - x:fx1 - x]
    a = (src[..., 3:4].astype(np.float32) / 255.0) * alpha
    dst = frame[fy0:fy1, fx0:fx1].astype(np.float32)
    frame[fy0:fy1, fx0:fx1] = (dst * (1 - a) + src[..., :3].astype(np.float32) * a + 0.5).astype(np.uint8)
