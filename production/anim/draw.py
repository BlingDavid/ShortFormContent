"""Tiny supersampled 2D drawing kit for code-animated characters.

Everything is drawn into local RGBA layers at SS x resolution and downsampled, so edges
are anti-aliased. Volume comes from concentric shaded blobs, not outlines.
"""
from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H = 1080, 1920
SS = 3


def hexc(h: str, a: int = 255):
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a


def lerp(a, b, t):
    return a + (b - a) * t


def mix(c1, c2, t):
    return tuple(int(round(lerp(x, y, t))) for x, y in zip(c1, c2))


def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def K(t, keys, ease=True):
    """Keyframe value at t. keys = [(time, value), ...] sorted; smoothstep between keys."""
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t <= t1:
            u = (t - t0) / max(1e-9, t1 - t0)
            return lerp(v0, v1, smooth(u) if ease else u)
    return keys[-1][1]


def pulse(t, t0, dur, peak=1.0):
    """0 -> peak -> 0 bump centred in [t0, t0+dur]."""
    u = (t - t0) / dur
    return peak * math.sin(math.pi * u) if 0 <= u <= 1 else 0.0


class Cv:
    """Supersampled RGBA layer covering scene rectangle box=(x0,y0,x1,y1)."""

    def __init__(self, box=(0, 0, W, H), ss=SS):
        self.x0, self.y0, self.x1, self.y1 = [int(v) for v in box]
        self.ss = ss
        self.im = Image.new("RGBA", ((self.x1 - self.x0) * ss, (self.y1 - self.y0) * ss), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)

    def P(self, x, y):
        return ((x - self.x0) * self.ss, (y - self.y0) * self.ss)

    def _blend(self, pts_px, fn, pad=4):
        """Draw with true alpha: render into a bbox-sized temp layer and alpha_composite it."""
        xs, ys = [p[0] for p in pts_px], [p[1] for p in pts_px]
        x0, y0 = max(0, int(min(xs)) - pad), max(0, int(min(ys)) - pad)
        x1, y1 = min(self.im.width, int(max(xs)) + pad), min(self.im.height, int(max(ys)) + pad)
        if x1 <= x0 or y1 <= y0:
            return
        tmp = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0))
        fn(ImageDraw.Draw(tmp), -x0, -y0)
        self.im.alpha_composite(tmp, (x0, y0))

    def poly(self, pts, fill):
        px = [self.P(x, y) for x, y in pts]
        if len(fill) == 4 and fill[3] < 255:
            if fill[3] > 0:
                self._blend(px, lambda dr, ox, oy: dr.polygon([(x + ox, y + oy) for x, y in px], fill=fill))
        else:
            self.d.polygon(px, fill=fill)

    def ell_pts(self, cx, cy, rx, ry, rot=0.0, n=56):
        c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
        out = []
        for i in range(n):
            a = 2 * math.pi * i / n
            x, y = rx * math.cos(a), ry * math.sin(a)
            out.append((cx + x * c - y * s, cy + x * s + y * c))
        return out

    def ellipse(self, cx, cy, rx, ry, fill, rot=0.0):
        self.poly(self.ell_pts(cx, cy, rx, ry, rot), fill)

    def blob(self, cx, cy, rx, ry, base, rot=0.0, dark=0.28, light=0.22, hi=(-0.28, -0.32), steps=9):
        """Volumetric ellipse: dark rim -> base -> lit core, highlight shifted toward `hi`."""
        c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
        rim = mix(base[:3], (30, 15, 10), dark) + (base[3] if len(base) > 3 else 255,)
        core = mix(base[:3], (255, 250, 235), light) + (base[3] if len(base) > 3 else 255,)
        for i in range(steps):
            u = i / (steps - 1)
            k = 1 - 0.78 * u
            ox, oy = hi[0] * rx * u * 0.9, hi[1] * ry * u * 0.9
            px, py = ox * c - oy * s, ox * s + oy * c
            col = mix(rim[:3], base[:3], min(1, u * 2.2)) if u < 0.45 else mix(base[:3], core[:3], (u - 0.45) / 0.55)
            self.ellipse(cx + px, cy + py, rx * k, ry * k, col + (rim[3],), rot)

    def capsule(self, x0, y0, x1, y1, r, fill):
        self.line([(x0, y0), (x1, y1)], fill, 2 * r)
        for x, y in ((x0, y0), (x1, y1)):
            self.ellipse(x, y, r, r, fill)

    def rrect(self, x0, y0, x1, y1, r, fill, outline=None, width=0):
        a, b = self.P(x0, y0), self.P(x1, y1)
        kw = dict(radius=r * self.ss, fill=fill, outline=outline, width=int(width * self.ss))
        if isinstance(fill, tuple) and len(fill) == 4 and fill[3] < 255:
            if fill[3] > 0:
                self._blend([a, b], lambda dr, ox, oy: dr.rounded_rectangle([(a[0] + ox, a[1] + oy), (b[0] + ox, b[1] + oy)], **kw))
        else:
            self.d.rounded_rectangle([a, b], **kw)

    def line(self, pts, fill, width):
        px = [self.P(x, y) for x, y in pts]
        w = max(1, int(width * self.ss))
        if len(fill) == 4 and fill[3] < 255:
            if fill[3] > 0:
                self._blend(px, lambda dr, ox, oy: dr.line([(x + ox, y + oy) for x, y in px], fill=fill, width=w, joint="curve"),
                            pad=w + 4)
        else:
            self.d.line(px, fill=fill, width=w, joint="curve")

    def rotated(self, painter, cx, cy, deg):
        """Run painter(cv2) on a sub-layer then rotate it about (cx,cy) into this layer."""
        sub = Cv((self.x0, self.y0, self.x1, self.y1), self.ss)
        painter(sub)
        c = ((cx - self.x0) * self.ss, (cy - self.y0) * self.ss)
        self.im.alpha_composite(sub.im.rotate(-deg, resample=Image.BICUBIC, center=c))
        self.d = ImageDraw.Draw(self.im)

    def flush(self, frame: Image.Image, alpha: float = 1.0):
        small = self.im.resize((self.im.width // self.ss, self.im.height // self.ss), Image.LANCZOS)
        if alpha < 1:
            small.putalpha(small.getchannel("A").point(lambda v: int(v * alpha)))
        frame.paste(small, (self.x0, self.y0), small)


def soft_shadow(frame, cx, cy, rx, ry, alpha=0.45, blur=18, color=(20, 8, 4)):
    pad = blur * 3
    lay = Image.new("L", (int(2 * rx + 2 * pad), int(2 * ry + 2 * pad)), 0)
    ImageDraw.Draw(lay).ellipse((pad, pad, pad + 2 * rx, pad + 2 * ry), fill=int(255 * alpha))
    lay = lay.filter(ImageFilter.GaussianBlur(blur))
    frame.paste(Image.new("RGB", lay.size, color), (int(cx - rx - pad), int(cy - ry - pad)), lay)


def vgrad(top, bottom, size=(W, H)):
    t = np.linspace(0, 1, size[1])[:, None, None]
    a = np.array(top, np.float32)[None, None, :]
    b = np.array(bottom, np.float32)[None, None, :]
    return Image.fromarray((a + (b - a) * t).repeat(size[0], axis=1).astype(np.uint8))


def radial_light(frame, cx, cy, r, color, strength=0.35):
    """Additive-ish warm light pool."""
    y, x = np.mgrid[0:frame.height, 0:frame.width].astype(np.float32)
    d = np.sqrt((x - cx) ** 2 + (y - cy) ** 2) / r
    m = np.clip(1 - d, 0, 1) ** 1.6 * strength
    arr = np.asarray(frame, np.float32)
    col = np.array(color, np.float32)[None, None, :]
    arr = arr * (1 - m[..., None]) + col * m[..., None]
    frame.paste(Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)))


def vignette(frame, strength=0.35):
    y, x = np.mgrid[0:frame.height, 0:frame.width].astype(np.float32)
    d = np.sqrt(((x - frame.width / 2) / (frame.width * 0.75)) ** 2 + ((y - frame.height / 2) / (frame.height * 0.7)) ** 2)
    m = 1 - np.clip(d, 0, 1) ** 2.2 * strength
    frame.paste(Image.fromarray(np.clip(np.asarray(frame, np.float32) * m[..., None], 0, 255).astype(np.uint8)))


def grain(frame, amount=5, seed=1):
    rng = np.random.default_rng(seed)
    n = rng.normal(0, amount, (frame.height, frame.width, 1)).astype(np.float32)
    frame.paste(Image.fromarray(np.clip(np.asarray(frame, np.float32) + n, 0, 255).astype(np.uint8)))
