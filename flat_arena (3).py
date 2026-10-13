"""
FLAT ARENA - FPS ثلاثي الأبعاد بستايل Flats
التثبيت:   pip install ursina
التشغيل:   python flat_arena.py

كل الأيقونات والصور (الأسلحة، القلب، الدرع، الجمجمة، الدم...) بتتولد بالكود وقت التشغيل،
فمش محتاج أي ملفات صور خارجية. والأصوات كمان بتتولد بالكود (فولدر flat_arena_sfx بيتعمل أول مرة).
الأسلحة: PISTOL SMG SHOTGUN SNIPER LAUNCHER + M4 و AKM (ARs) + MINIGUN (أقوى سلاح) + HEADHUNTER (ريفولفر فضي، سلاح خاص).

القائمة الرئيسية: اختار الطور (MODE) والماب والصعوبة وموجة البداية وحتى 3 أسلحة، وبعدين START.
الأطوار:  WAVES (الكلاسيك) | ARMS RACE (تبدأ بأضعف سلاح وكل ما تقتل أكتر السلاح يقوى)
          SURVIVAL (أعداء بلا نهاية) | TIME ATTACK (اقتل أكبر عدد قبل ما الوقت يخلص)

التحكم داخل اللعبة:
  W A S D = حركة     الماوس = نظر      Space = قفز       Left Shift = داش
  كليك يسار = إطلاق (اضغط مطولاً للأوتوماتيك)    R = إعادة تعبئة
  كليك يمين (اضغط مطولاً) = سكوب: الكاميرا بتدخل ورا السلاح نفسه وبتبص من الشاخص (السنايبر بيفتح سكوب كامل)
  V = تبديل بين منظور شخص ثالث (الافتراضي) ومنظور شخص أول
  1..4 أو عجلة الماوس = تبديل السلاح     TAB = قائمة المهارات
  Esc = إيقاف اللعبة (كمّل / إعادة من الأول / إعدادات / قائمة رئيسية)
  Enter = إعادة اللعب بعد الخسارة
"""
import random
import math
import json
import os
from pathlib import Path
from ursina import *

# ================================================================ مولّد الأيقونات (Pillow)
from PIL import Image, ImageDraw

SS = 4  # supersampling


def _hex(h, a=255):
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def _shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c[:3]) + (c[3],)


INK_RGB = _hex('#2b2d42')
WHITE = _hex('#ffffff')
METAL = _hex('#8d99ae')
METAL_D = _hex('#5c677d')
GLOW = _hex('#ffe66d')


class Canvas:
    """Canvas بيرسم بإحداثيات ثابتة (w,h) وبيصغّر بنعومة."""

    def __init__(self, w, h, bg=None):
        self.w, self.h = w, h
        self.im = Image.new('RGBA', (w * SS, h * SS), bg or (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)

    def P(self, pts):
        return [(x * SS, y * SS) for x, y in pts]

    def poly(self, pts, fill, outline=INK_RGB, ow=3):
        p = self.P(pts)
        self.d.polygon(p, fill=fill)
        if outline and ow:
            self.d.line(p + [p[0]], fill=outline, width=int(ow * SS), joint='curve')

    def rrect(self, box, r, fill, outline=INK_RGB, ow=3):
        x0, y0, x1, y1 = box
        self.d.rounded_rectangle([x0 * SS, y0 * SS, x1 * SS, y1 * SS], radius=r * SS, fill=fill,
                                 outline=outline if ow else None, width=int(ow * SS))

    def ell(self, box, fill, outline=INK_RGB, ow=3):
        x0, y0, x1, y1 = box
        self.d.ellipse([x0 * SS, y0 * SS, x1 * SS, y1 * SS], fill=fill,
                       outline=outline if ow else None, width=int(ow * SS))

    def line(self, pts, fill, w=3):
        self.d.line(self.P(pts), fill=fill, width=int(w * SS), joint='curve')

    def arc(self, box, a0, a1, fill, w=3):
        x0, y0, x1, y1 = box
        self.d.arc([x0 * SS, y0 * SS, x1 * SS, y1 * SS], a0, a1, fill=fill, width=int(w * SS))

    def done(self):
        return self.im.resize((self.w, self.h), Image.LANCZOS)


# ------------------------------------------------------------------ أيقونات الأسلحة (منظر جانبي، متجهة لليمين)
def gun_icon(name, accent, w=256, h=128):
    c = Canvas(w, h)
    A = _hex(accent)
    A2 = _shade(A, .7)
    K = INK_RGB
    M, MD = METAL, METAL_D
    if name == 'PISTOL':
        c.poly([(70, 62), (112, 62), (100, 112), (70, 112)], K)                       # القبضة
        c.poly([(78, 66), (108, 66), (98, 106), (78, 106)], _shade(K, 1.6), None, 0)
        c.rrect((54, 36, 206, 66), 6, A)                                              # السلايد
        c.rrect((54, 36, 206, 46), 5, _shade(A, 1.25), None, 0)
        c.rrect((196, 42, 222, 58), 3, MD)                                            # الماسورة
        for x in (70, 80, 90, 100):
            c.line([(x, 41), (x - 3, 62)], A2, 2)
        c.rrect((54, 30, 66, 38), 2, K)                                               # الشاخص
        c.rrect((190, 30, 202, 38), 2, K)
        c.arc((100, 58, 140, 96), 0, 180, K, 4)                                       # حلقة الزناد
        c.line([(118, 66), (118, 80)], GLOW, 4)
    elif name == 'SMG':
        c.poly([(120, 60), (150, 60), (146, 120), (122, 120)], K)                     # الخزنة
        c.poly([(128, 64), (144, 64), (141, 112), (126, 112)], _shade(K, 1.6), None, 0)
        c.poly([(64, 66), (92, 66), (80, 108), (62, 108)], K)                         # القبضة
        c.rrect((36, 40, 190, 68), 6, A)                                              # الجسم
        c.rrect((36, 40, 190, 50), 5, _shade(A, 1.25), None, 0)
        c.rrect((186, 46, 240, 60), 3, MD)                                            # الماسورة
        c.rrect((226, 42, 244, 64), 3, K)
        c.rrect((8, 44, 40, 62), 4, MD)                                               # الأبو كتف
        c.rrect((90, 28, 140, 42), 4, K)                                              # السكوب الصغير
        c.rrect((96, 31, 134, 36), 2, GLOW, None, 0)
        for x in (150, 160, 170):
            c.line([(x, 44), (x, 64)], A2, 2)
    elif name == 'SHOTGUN':
        c.poly([(6, 56), (62, 50), (62, 84), (14, 100)], _hex('#8d5524'))             # الكعب خشب
        c.poly([(14, 62), (58, 56), (58, 70), (18, 82)], _hex('#b07a45'), None, 0)
        c.rrect((60, 46, 130, 76), 6, A)                                              # الجسم
        c.rrect((60, 46, 130, 56), 5, _shade(A, 1.25), None, 0)
        c.rrect((120, 40, 246, 52), 5, MD)                                            # الماسورة العلوية
        c.rrect((120, 54, 246, 66), 5, M)                                             # الماسورة التحتية
        c.rrect((236, 38, 250, 68), 3, K)
        c.rrect((132, 68, 196, 86), 6, _hex('#8d5524'))                               # المقبض الأمامي
        c.rrect((136, 71, 192, 76), 2, _hex('#b07a45'), None, 0)
        c.line([(86, 76), (86, 92)], K, 4)
    elif name == 'SNIPER':
        c.rrect((4, 52, 70, 80), 6, _shade(A, .85))                                   # الكعب
        c.poly([(66, 56), (120, 52), (120, 82), (82, 96), (66, 82)], K)               # الجسم
        c.rrect((100, 52, 164, 74), 5, A)
        c.rrect((100, 52, 164, 60), 4, _shade(A, 1.25), None, 0)
        c.rrect((160, 58, 252, 68), 4, MD)                                            # الماسورة الطويلة
        c.rrect((244, 55, 256, 71), 3, K)
        c.rrect((96, 24, 190, 44), 9, K)                                              # السكوب الكبير
        c.rrect((104, 28, 182, 36), 4, _hex('#4cc9f0'), None, 0)
        c.ell((90, 22, 112, 46), MD)
        c.ell((172, 22, 196, 46), MD)
        c.line([(120, 44), (120, 54)], K, 4)
        c.line([(168, 44), (168, 56)], K, 4)
        c.line([(176, 68), (196, 98)], K, 4)                                          # الحامل الثنائي
        c.line([(184, 68), (210, 96)], K, 4)
    elif name == 'LAUNCHER':
        c.rrect((20, 40, 200, 80), 14, A)                                             # الأنبوب
        c.rrect((20, 40, 200, 54), 12, _shade(A, 1.3), None, 0)
        c.rrect((190, 34, 236, 86), 8, K)                                             # الفوهة
        c.ell((218, 44, 244, 76), _hex('#ffb703'))
        c.ell((226, 52, 238, 68), K, None, 0)
        for x in (60, 100, 140):                                                      # خطوط التحذير
            c.poly([(x, 40), (x + 14, 40), (x + 4, 80), (x - 10, 80)], GLOW, None, 0)
        c.poly([(86, 80), (134, 80), (122, 116), (96, 116)], K)                       # القبضة
        c.rrect((10, 50, 26, 70), 4, MD)
        c.rrect((120, 24, 150, 40), 4, K)                                             # الشاخص
        c.rrect((124, 27, 146, 33), 2, _hex('#4cc9f0'), None, 0)
    elif name == 'HEADHUNTER':   # ريفولفر فضي لامع
        WD, WL = _hex('#8d5524'), _hex('#b07a45')
        SIL, SILD = _hex('#f1f5fa'), _hex('#9aa6b8')
        c.poly([(36, 66), (84, 62), (98, 76), (76, 120), (34, 108)], WD)              # القبضة خشب
        c.poly([(46, 74), (78, 70), (66, 106), (46, 100)], WL, None, 0)
        c.rrect((52, 38, 152, 78), 8, A)                                              # الإطار (فضي)
        c.rrect((52, 38, 152, 48), 6, WHITE, None, 0)
        c.rrect((152, 42, 244, 58), 4, SILD)                                          # الماسورة
        c.rrect((152, 42, 244, 48), 3, WHITE, None, 0)
        c.rrect((152, 56, 214, 68), 4, SILD)                                          # تحت الماسورة
        c.rrect((236, 40, 254, 60), 3, K)                                             # الفوهة
        c.rrect((224, 32, 234, 42), 2, SIL)                                           # الشاخص
        c.rrect((96, 30, 146, 84), 10, SIL)                                           # الأسطوانة
        c.rrect((100, 33, 112, 80), 5, WHITE, None, 0)
        for x in (108, 121, 134):
            c.line([(x, 34), (x, 80)], SILD, 3)
        c.poly([(46, 34), (62, 24), (72, 38), (58, 48)], SILD)                        # الهامر
        c.arc((96, 74, 136, 110), 0, 180, K, 4)                                       # حلقة الزناد
        c.line([(114, 78), (118, 92)], SILD, 4)
        c.ell((64, 50, 84, 70), WHITE, K, 2)                                          # جمجمة صغيرة
        c.ell((68, 56, 73, 62), K, None, 0)
        c.ell((76, 56, 81, 62), K, None, 0)
        for cx, cy, r in ((186, 38, 9), (132, 30, 6), (84, 40, 5)):                   # لمعة
            c.poly([(cx, cy - r), (cx + r * .3, cy - r * .3), (cx + r, cy), (cx + r * .3, cy + r * .3),
                    (cx, cy + r), (cx - r * .3, cy + r * .3), (cx - r, cy), (cx - r * .3, cy - r * .3)],
                   WHITE, None, 0)
    elif name == 'M4':
        c.poly([(6, 52), (52, 52), (52, 76), (14, 84)], K)                            # الأبو كتف
        c.rrect((2, 50, 12, 84), 2, MD)
        c.rrect((50, 44, 136, 76), 5, A)                                              # الجسم
        c.rrect((50, 44, 136, 53), 4, _shade(A, 1.25), None, 0)
        c.rrect((60, 34, 112, 46), 4, K)                                              # مقبض الحمل
        c.rrect((70, 37, 102, 41), 2, _hex('#4cc9f0'), None, 0)
        c.rrect((136, 48, 206, 72), 4, K)                                             # الحماية
        for x in (146, 158, 170, 182, 194):
            c.line([(x, 52), (x, 68)], MD, 2)
        c.rrect((204, 54, 244, 64), 3, MD)                                            # الماسورة
        c.rrect((240, 50, 254, 68), 3, K)
        c.poly([(196, 36), (204, 36), (204, 48), (196, 48)], K)                       # الشاخص
        c.poly([(66, 76), (88, 76), (80, 114), (60, 110)], K)                         # القبضة
        c.poly([(100, 76), (124, 76), (130, 116), (108, 118)], MD)                    # الخزنة
        c.poly([(106, 80), (116, 80), (120, 110), (112, 111)], _shade(MD, 1.3), None, 0)
        c.arc((84, 70, 106, 92), 0, 180, K, 3)
    elif name == 'AKM':
        WD, WL = _hex('#8d5524'), _hex('#b07a45')
        c.poly([(4, 56), (52, 52), (52, 80), (12, 92)], WD)                           # الكعب خشب
        c.poly([(14, 62), (48, 58), (48, 70), (18, 80)], WL, None, 0)
        c.rrect((50, 46, 130, 76), 4, A)                                              # الجسم
        c.rrect((50, 42, 124, 52), 3, _shade(A, 1.25))
        c.rrect((130, 48, 194, 76), 5, WD)                                            # الحماية خشب
        c.rrect((136, 52, 188, 58), 3, WL, None, 0)
        c.rrect((130, 38, 206, 46), 3, MD)                                            # أنبوب الغاز
        c.rrect((192, 54, 242, 64), 3, MD)                                            # الماسورة
        c.rrect((236, 48, 254, 70), 3, K)                                             # كاتم الارتداد
        c.poly([(226, 36), (234, 36), (234, 54), (226, 54)], K)                       # الشاخص
        c.poly([(60, 76), (82, 76), (74, 114), (54, 108)], WD)                        # القبضة
        c.poly([(98, 76), (124, 76), (138, 98), (146, 120), (120, 120), (104, 98)], MD)   # الخزنة المقوسة
        c.line([(108, 84), (126, 100), (130, 112)], _shade(MD, 1.4), 3)
        c.arc((80, 70, 102, 92), 0, 180, K, 3)
    elif name == 'MINIGUN':
        for k, y in enumerate((44, 52, 60, 68)):                                      # 6 مواسير (نشوف 4)
            c.rrect((100, y, 236, y + 8), 3, M if k % 2 else MD)
        c.rrect((226, 38, 240, 80), 4, K)                                             # حلقة أمامية
        c.rrect((160, 38, 170, 80), 3, K)                                             # حلقة وسط
        c.rrect((40, 36, 112, 84), 10, A)                                             # الجسم
        c.rrect((40, 36, 112, 48), 8, _shade(A, 1.3), None, 0)
        c.rrect((14, 48, 44, 72), 5, MD)                                              # الخلفية
        c.rrect((60, 22, 100, 36), 5, K)                                              # المقبض
        c.rrect((52, 84, 124, 122), 6, K)                                             # صندوق الذخيرة
        for x in (60, 72, 84, 96, 108):
            c.rrect((x, 92, x + 8, 114), 2, GLOW, None, 0)
        c.poly([(130, 84), (150, 84), (146, 116), (132, 116)], K)                     # قبضة
    return c.done()


def badge_bg(w=180, h=150, fill='#2b2d42', border='#ffffff', bw=4, r=18, alpha=215):
    c = Canvas(w, h)
    f = _hex(fill, alpha)
    c.rrect((bw, bw, w - bw, h - bw), r, f, _hex(border), bw)
    return c.done()


def panel_bg(w=256, h=128, fill='#2b2d42', alpha=190, r=22):
    c = Canvas(w, h)
    c.rrect((2, 2, w - 2, h - 2), r, _hex(fill, alpha), None, 0)
    return c.done()


# ------------------------------------------------------------------ أيقونات الواجهة (64x64)
def heart_icon(col='#ff4d6d', s=64):
    c = Canvas(s, s)
    C1 = _hex(col)
    pts = []
    for i in range(0, 361, 6):
        t = math.radians(i)
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((s / 2 + x * s / 38, s / 2 - y * s / 38 - 1))
    c.poly(pts, C1, INK_RGB, 3)
    c.ell((14, 14, 26, 24), _hex('#ffffff', 170), None, 0)
    return c.done()


def shield_icon(col='#4cc9f0', s=64):
    c = Canvas(s, s)
    C1 = _hex(col)
    pts = [(32, 6), (54, 14), (54, 32), (46, 46), (32, 58), (18, 46), (10, 32), (10, 14)]
    c.poly(pts, C1, INK_RGB, 3)
    c.poly([(32, 12), (48, 18), (48, 32), (32, 52), (32, 12)], _shade(C1, .75), None, 0)
    c.line([(32, 16), (32, 46)], WHITE, 3)
    c.line([(20, 26), (44, 26)], WHITE, 3)
    return c.done()


def bullet_icon(s=64, col='#ffb703'):
    c = Canvas(s, s)
    c.rrect((24, 22, 40, 56), 3, _hex(col))
    c.poly([(24, 24), (32, 6), (40, 24)], _hex('#e9c46a'))
    c.rrect((22, 52, 42, 60), 2, METAL_D)
    c.line([(28, 28), (28, 50)], _hex('#ffffff', 160), 2)
    return c.done()


def skull_icon(s=64):
    c = Canvas(s, s)
    c.ell((10, 6, 54, 46), WHITE)
    c.rrect((20, 38, 44, 58), 4, WHITE)
    c.ell((18, 20, 29, 33), INK_RGB, None, 0)
    c.ell((35, 20, 46, 33), INK_RGB, None, 0)
    c.poly([(32, 34), (28, 42), (36, 42)], INK_RGB, None, 0)
    for x in (26, 32, 38):
        c.line([(x, 48), (x, 58)], INK_RGB, 2)
    return c.done()


def flag_icon(s=64, col='#ff7096'):
    c = Canvas(s, s)
    c.rrect((12, 6, 18, 60), 2, _hex('#ffffff'))
    c.poly([(18, 8), (54, 16), (18, 32)], _hex(col))
    c.poly([(18, 8), (36, 12), (18, 18)], _hex('#ffffff', 150), None, 0)
    return c.done()


def star_icon(s=64, col='#ffb703'):
    c = Canvas(s, s)
    pts = []
    for i in range(10):
        r = 28 if i % 2 == 0 else 12
        a = math.radians(-90 + i * 36)
        pts.append((32 + r * math.cos(a), 34 + r * math.sin(a)))
    c.poly(pts, _hex(col))
    return c.done()


def bolt_icon(s=64, col='#ffe66d'):
    c = Canvas(s, s)
    c.poly([(38, 4), (14, 36), (28, 36), (22, 60), (50, 24), (34, 24)], _hex(col))
    return c.done()


def crosshair_icon(s=64, col='#ffffff'):
    c = Canvas(s, s)
    for (a, b) in [((32, 4), (32, 22)), ((32, 42), (32, 60)), ((4, 32), (22, 32)), ((42, 32), (60, 32))]:
        c.line([a, b], INK_RGB, 7)
    for (a, b) in [((32, 5), (32, 21)), ((32, 43), (32, 59)), ((5, 32), (21, 32)), ((43, 32), (59, 32))]:
        c.line([a, b], _hex(col), 3)
    c.ell((29, 29, 35, 35), _hex('#e63946'), None, 0)
    return c.done()


def hitmark_icon(s=64, col='#ffffff'):
    c = Canvas(s, s)
    for (a, b) in [((14, 14), (26, 26)), ((50, 14), (38, 26)), ((14, 50), (26, 38)), ((50, 50), (38, 38))]:
        c.line([a, b], INK_RGB, 8)
    for (a, b) in [((14, 14), (26, 26)), ((50, 14), (38, 26)), ((14, 50), (26, 38)), ((50, 50), (38, 38))]:
        c.line([a, b], _hex(col), 4)
    return c.done()


def fist_icon(s=64):   # أيقونة الضرر: انفجار
    c = Canvas(s, s)
    pts = []
    for i in range(16):
        r = 28 if i % 2 == 0 else 15
        a = math.radians(i * 22.5)
        pts.append((32 + r * math.cos(a), 32 + r * math.sin(a)))
    c.poly(pts, _hex('#fb8500'))
    c.ell((20, 20, 44, 44), _hex('#ffe66d'), None, 0)
    return c.done()


def speed_icon(s=64):  # سهم/أجنحة
    c = Canvas(s, s)
    for k, col in enumerate(('#06d6a0', '#2a9d8f')):
        o = k * 12
        c.poly([(8 + o, 14), (30 + o, 32), (8 + o, 50), (16 + o, 32)], _hex(col))
    c.poly([(40, 14), (58, 32), (40, 50), (46, 32)], _hex('#ffffff'))
    return c.done()


def reload_icon(s=64):
    c = Canvas(s, s)
    c.arc((10, 10, 54, 54), 30, 320, INK_RGB, 11)
    c.arc((10, 10, 54, 54), 30, 320, _hex('#8ecae6'), 6)
    c.poly([(40, 4), (58, 20), (36, 24)], _hex('#8ecae6'))
    return c.done()


def head_icon(s=64):
    c = Canvas(s, s)
    c.ell((14, 8, 50, 48), _hex('#ffcfa3'))
    c.rrect((24, 44, 40, 58), 3, _hex('#ffcfa3'))
    for r in (28, 20, 12):
        c.arc((32 - r, 28 - r, 32 + r, 28 + r), 0, 360, _hex('#e63946'), 3)
    c.ell((29, 25, 35, 31), _hex('#e63946'), None, 0)
    return c.done()


def plus_icon(s=64, col='#ff7096'):
    c = Canvas(s, s)
    c.rrect((4, 4, s - 4, s - 4), 14, _hex(col), INK_RGB, 3)
    c.line([(32, 16), (32, 48)], WHITE, 8)
    c.line([(16, 32), (48, 32)], WHITE, 8)
    return c.done()


# ------------------------------------------------------------------ دم وفيجنيت
def blood_splat(seed=0, s=128, col='#c1121f'):
    rng = random.Random(seed)
    c = Canvas(s, s)
    base = _hex(col)
    dark = _shade(base, .72)
    cx = cy = s / 2
    for k in range(2):
        cc = dark if k == 0 else base
        rr = s * (.26 if k == 0 else .19)
        # بقعة غير منتظمة
        pts = []
        for i in range(18):
            a = math.tau * i / 18
            r = rr * rng.uniform(.8, 1.2)
            pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
        c.poly(pts, cc, None, 0)
        for _ in range(6):
            a = rng.uniform(0, math.tau)
            dist = rng.uniform(rr * 1.0, rr * 1.55)
            r = rng.uniform(s * .025, s * .06) * (1.15 if k == 0 else .85)
            x, y = cx + math.cos(a) * dist, cy + math.sin(a) * dist
            c.line([(cx + math.cos(a) * rr * .7, cy + math.sin(a) * rr * .7), (x, y)], cc, r * .9)
            c.ell((x - r, y - r, x + r, y + r), cc, None, 0)
    c.ell((cx - s * .09, cy - s * .12, cx - s * .03, cy - s * .07), _hex('#ffffff', 90), None, 0)
    return c.done()


def flash_icon(s=64):
    c = Canvas(s, s)
    pts = []
    for i in range(16):
        r = 30 if i % 2 == 0 else 11
        a = math.radians(i * 22.5)
        pts.append((32 + r * math.cos(a), 32 + r * math.sin(a)))
    c.poly(pts, _hex('#ffb703'), None, 0)
    pts = []
    for i in range(16):
        r = 20 if i % 2 == 0 else 8
        a = math.radians(i * 22.5 + 11)
        pts.append((32 + r * math.cos(a), 32 + r * math.sin(a)))
    c.poly(pts, _hex('#ffe66d'), None, 0)
    c.ell((24, 24, 40, 40), WHITE, None, 0)
    return c.done()


def vignette(s=128, col='#d00000'):
    im = Image.new('RGBA', (s, s))
    px = im.load()
    cc = _hex(col)
    for y in range(s):
        for x in range(s):
            dx, dy = (x - s / 2) / (s / 2), (y - s / 2) / (s / 2)
            d = min(1.4, math.hypot(dx, dy))
            a = max(0.0, (d - .55) / .85)
            a = min(1.0, a * a * 1.5)
            px[x, y] = (cc[0], cc[1], cc[2], int(255 * a))
    return im


ICON_NAMES = ['heart', 'shield', 'bullet', 'skull', 'flag', 'star', 'bolt', 'crosshair', 'hitmark',
              'fist', 'speed', 'reload', 'head', 'plus']


try:
    _BASE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _BASE = os.getcwd()

app = Ursina(title="Flat Arena")


def C(h):
    return color.hex(h)


INK = C('#2b2d42')
GOLD = C('#ffb703')
FLASH = C('#ffe66d')
WHITE_C = color.white
BLOOD_COLS = (C('#c1121f'), C('#e5383b'), C('#9d0208'))

# ================================================================ توليد الأيقونات كـ Textures
ICON_DIR = os.path.join(_BASE, 'flat_arena_icons')


def make_tex(im, name):
    """بيحول صورة PIL لـ Texture في ursina (ولو فشل بيحفظها كملف PNG ويحملها)."""
    try:
        t = Texture(im)
        if t.width > 0:
            return t
    except Exception:
        pass
    os.makedirs(ICON_DIR, exist_ok=True)
    p = os.path.join(ICON_DIR, name + '.png')
    im.save(p)
    return Texture(Path(p))


T = {}
for _n, _f in [('heart', heart_icon), ('shield', shield_icon), ('bullet', bullet_icon),
               ('skull', skull_icon), ('flag', flag_icon), ('star', star_icon), ('bolt', bolt_icon),
               ('crosshair', crosshair_icon), ('hitmark', hitmark_icon), ('fist', fist_icon),
               ('speed', speed_icon), ('reload', reload_icon), ('head', head_icon),
               ('plus', plus_icon), ('flash', flash_icon)]:
    T[_n] = make_tex(_f(), 'icon_' + _n)
T['panel'] = make_tex(panel_bg(), 'panel')
T['slot'] = make_tex(badge_bg(border='#cdb4db', bw=3), 'slot')
T['slot_sel'] = make_tex(badge_bg(fill='#3d405b', border='#ffb703', bw=6, alpha=245), 'slot_sel')
T['vig'] = make_tex(vignette(), 'vignette')
for _i in range(3):
    T['splat%d' % _i] = make_tex(blood_splat(_i), 'splat%d' % _i)

# ================================================================ الإعدادات (الماب / الصعوبة / الأطوار)
MAPS = {
    # ---- المابات الأصلية
    'PLAZA': dict(size=40, sky='#bde0fe', ground='#9ad1a4', wall='#ff7096', gen='random', count=18, seed=7,
                  pillars=['#ffb703', '#fb8500', '#8ecae6', '#219ebc', '#cdb4db', '#ffafcc'],
                  shapes=['round', 'round', 'tower', 'box'],
                  desc='Open plaza with cover pillars'),
    'MAZE':  dict(size=40, sky='#ffd6a5', ground='#e9c46a', wall='#e76f51', gen='maze', seed=3,
                  pillars=['#f4a261', '#e76f51', '#2a9d8f', '#8d5524'],
                  desc='Tight corridors - close combat'),
    'YARD':  dict(size=40, sky='#dbe7ff', ground='#b8c0ff', wall='#5e60ce', gen='platforms', seed=5,
                  pillars=['#ffd166', '#06d6a0', '#ef476f', '#ffffff'],
                  shapes=['round', 'box'], plain_below=1.0,
                  desc='Jumpable platforms - fight from above'),
    'NIGHT': dict(size=55, sky='#1b1b2f', ground='#3d405b', wall='#7209b7', gen='random', count=34, seed=11,
                  pillars=['#f72585', '#4cc9f0', '#4361ee', '#b5179e', '#ffb703'],
                  shapes=['round', 'tower', 'box'],
                  desc='Huge dark arena - long range'),
    # ---- مابات جديدة وأكبر
    'FORTRESS': dict(size=80, sky='#cfe8ff', ground='#8fb996', wall='#6c757d', gen='fortress', seed=21,
                     wall_h=10, count=26,
                     pillars=['#adb5bd', '#ced4da', '#8d99ae', '#b08968', '#ffb703'],
                     shapes=['tower', 'round'],
                     desc='Castle with gates, towers and crates outside'),
    'PYRAMIDS': dict(size=85, sky='#ffe8a3', ground='#f1d58a', wall='#e09f3e', gen='pyramids', seed=33,
                     count=16, pyr=[(-44, -44), (44, -44), (-44, 44), (44, 44), (0, 62), (0, -62)],
                     pillars=['#e9c46a', '#f4a261', '#fefae0', '#ccd5ae', '#e76f51'],
                     shapes=['round', 'tower', 'boulder'], plain_below=4.5,
                     desc='Six climbable stepped pyramids - jump up the tiers'),
    'LABYRINTH': dict(size=74, sky='#d8c3ff', ground='#cdb4db', wall='#5e548e', gen='labyrinth', seed=44,
                      cells=13, cell=11, braid=.4,
                      pillars=['#9f86c0', '#be95c4', '#e0b1cb', '#7251b5'],
                      shapes=['tower'],
                      desc='Giant maze with loops - get lost, ambush them'),
    'CITY': dict(size=90, sky='#a0c4ff', ground='#6c757d', wall='#343a40', gen='city', seed=55,
                 wall_h=14, pitch=26, hmax=13,
                 pillars=['#e5e5e5', '#adb5bd', '#ffadad', '#ffd6a5', '#caffbf', '#9bf6ff', '#a0c4ff'],
                 shapes=['tower', 'tower', 'round'],
                 desc='City blocks, streets, cars and tall buildings'),
    'CANYON': dict(size=110, sky='#ffcfa3', ground='#d4a373', wall='#9c4f2f', gen='canyon', seed=66,
                   wall_h=12, count=34,
                   pillars=['#bc6c25', '#dda15e', '#a44a3f', '#c38e70'],
                   shapes=['boulder', 'boulder', 'round'],
                   desc='Long rock ridges and boulders - sniper heaven'),
    'WASTELAND': dict(size=150, sky='#9fb4c7', ground='#a9b388', wall='#4a4e69', gen='random', seed=77,
                      count=110, s=(2, 6), h=(2, 9), wall_h=12,
                      pillars=['#6b705c', '#a5a58d', '#b7b7a4', '#ddbea9', '#cb997e'],
                      shapes=['boulder', 'round', 'tower', 'box'],
                      desc='MASSIVE open field 300 x 300 m - bring a sniper'),
}
MAP_NAMES = list(MAPS)

DIFFS = {
    'EASY':   dict(hp=.7,  spd=.85, dmg=.6,  cnt=.7,  score=.75),
    'NORMAL': dict(hp=1.0, spd=1.0, dmg=1.0, cnt=1.0, score=1.0),
    'HARD':   dict(hp=1.4, spd=1.15, dmg=1.4, cnt=1.3, score=1.5),
    'INSANE': dict(hp=2.0, spd=1.3, dmg=2.0, cnt=1.7, score=2.5),
}
DIFF_NAMES = list(DIFFS)
START_WAVES = [1, 3, 5, 8, 12]

MODES = ['WAVES', 'ARMS RACE', 'SURVIVAL', 'TIME ATTACK']
MODE_DESC = {
    'WAVES': 'Classic: clear every wave, earn skill points',
    'ARMS RACE': 'Start with the weakest gun - more kills = stronger gun',
    'SURVIVAL': 'Endless enemies, level up every few kills',
    'TIME ATTACK': 'Kill as many as you can before time runs out',
}
KILLS_PER_LEVEL = 8      # في الأطوار المستمرة: كل كام قتلة يزيد المستوى
# أرقام الأسلحة في WEAPONS:  0 PISTOL 1 SMG 2 SHOTGUN 3 SNIPER 4 LAUNCHER 5 HEADHUNTER 6 M4 7 AKM 8 MINIGUN
ARMS_LADDER = [0, 1, 2, 6, 7, 3, 4, 5, 8]   # ترتيب الأسلحة في ARMS RACE (من الأضعف للأقوى)
LOADOUT_IDS = [0, 1, 2, 3, 4, 6, 7, 8]       # الأسلحة اللي ينفع تختارها في القائمة (الهيدهنتر سلاح خاص)
SPECIAL = 5                         # رقم سلاح HEADHUNTER في WEAPONS

CFG = dict(mode=0, map=0, diff=1, start=0, loadout=[0, 1, 2])


def D():
    return DIFFS[DIFF_NAMES[CFG['diff']]]


# ---------------------------------------------------------------- إعدادات اللاعب (بتتحفظ في ملف)
SET_DEFAULT = dict(sens=1.0, fov=90, aim_toggle=False, crosshair=True, shake=True, blood=True,
                   vignette=True, show_fps=False, auto_reload=True, enemy_amt=1.0, enemy_spd=1.0,
                   dmg_taken=1.0, special_chance=30, arms_kills=5, time_limit=90, volume=.8, quality=0)
SETTINGS_FILE = os.path.join(_BASE, 'flat_arena_settings.json')

# ---- مستويات الجودة (للأجهزة الضعيفة): 0 = LOW  1 = MEDIUM  2 = HIGH
QUALITY_NAMES = ('LOW', 'MEDIUM', 'HIGH')
QUAL = (
    dict(max_en=12, fx=.3, decals=4,  cam_every=4, fog=(35, 85),   far=95,  detail=False, simple_map=True),
    dict(max_en=25, fx=.6, decals=12, cam_every=2, fog=(60, 140),  far=170, detail=True,  simple_map=False),
    dict(max_en=45, fx=1.0, decals=26, cam_every=1, fog=None,      far=1000, detail=True,  simple_map=False),
)


def load_settings():
    s = dict(SET_DEFAULT)
    try:
        with open(SETTINGS_FILE, encoding='utf-8') as f:
            data = json.load(f)
        for k, v in data.items():
            if (k in s and isinstance(v, (bool, int, float))
                    and isinstance(v, bool) == isinstance(s[k], bool)):
                s[k] = v
    except Exception:
        pass
    return s


SET = load_settings()


def Q():
    return QUAL[int(clamp(SET['quality'], 0, 2))]


def save_settings():
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(SET, f)
    except Exception:
        pass


def shake(duration, magnitude):
    if SET['shake']:
        S['shk_t'] = max(S['shk_t'], duration)
        S['shk_m'] = max(S['shk_m'], magnitude)


# ---------------------------------------------------------------- أفضل نتيجة (بتتحفظ في ملف)
SCORE_FILE = os.path.join(_BASE, 'flat_arena_scores.json')


def load_scores():
    try:
        with open(SCORE_FILE, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


BEST = load_scores()


def best_key():
    base = f"{MAP_NAMES[CFG['map']]}|{DIFF_NAMES[CFG['diff']]}"
    m = MODES[CFG['mode']]
    return base if m == 'WAVES' else f"{m}|{base}"


def get_best():
    return BEST.get(best_key(), {'score': 0, 'wave': 0})


def save_best(score, wave):
    """ترجع True لو دي أفضل نتيجة جديدة."""
    if score <= 0:
        return False
    if score > get_best()['score']:
        BEST[best_key()] = {'score': score, 'wave': wave}
        try:
            with open(SCORE_FILE, 'w', encoding='utf-8') as f:
                json.dump(BEST, f)
        except Exception:
            pass
        return True
    return False


# ================================================================ العالم / الماب
ARENA = 40
pillars = []
world = []
DECALS = []


def gen_random(cfg, rng):
    size, out, tries = cfg['size'], [], 0
    hlo, hhi = cfg.get('h', (3, 8))
    slo, shi = cfg.get('s', (2, 4))
    while len(out) < cfg['count'] and tries < 900:
        tries += 1
        h, sx, sz = rng.uniform(hlo, hhi), rng.uniform(slo, shi), rng.uniform(slo, shi)
        x, z = rng.uniform(-size + 6, size - 6), rng.uniform(-size + 6, size - 6)
        if math.hypot(x, z) < 10:
            continue
        out.append((x, z, sx, sz, h))
    return out


def gen_maze(cfg, rng):
    H = 5
    segs = [(-25, -14, 14, 2), (25, -14, 14, 2), (-25, 14, 14, 2), (25, 14, 14, 2),
            (-14, -25, 2, 14), (14, -25, 2, 14), (-14, 25, 2, 14), (14, 25, 2, 14),
            (0, 9, 8, 2), (0, -9, 8, 2), (9, 0, 2, 8), (-9, 0, 2, 8),
            (-31, 0, 6, 2), (31, 0, 6, 2), (0, -32, 2, 6), (0, 32, 2, 6)]
    return [(x, z, sx, sz, H) for x, z, sx, sz in segs]


def gen_platforms(cfg, rng):
    out = []
    for gx in (-24, -8, 8, 24):
        for gz in (-24, -8, 8, 24):
            if abs(gx) <= 8 and abs(gz) <= 8:
                continue
            s = rng.uniform(5, 7)
            out.append((gx, gz, s, s, rng.choice([1.4, 1.4, 2.8])))
    return out


def gen_fortress(cfg, rng):
    """قلعة: سور بأربع بوابات + أبراج في الأركان + مباني جوه + صناديق برا."""
    out = []
    R, t, H, gate = 34, 3, 7, 7
    for sgn in (-1, 1):
        out.append((sgn * (R + gate) / 2, R, R - gate, t, H))      # سور شمال
        out.append((sgn * (R + gate) / 2, -R, R - gate, t, H))     # سور جنوب
        out.append((R, sgn * (R + gate) / 2, t, R - gate, H))      # سور شرق
        out.append((-R, sgn * (R + gate) / 2, t, R - gate, H))     # سور غرب
    for cx in (-R, R):
        for cz in (-R, R):
            out.append((cx, cz, 8, 8, 12))                         # أبراج الأركان
    for cx in (-16, 16):
        for cz in (-16, 16):
            out.append((cx, cz, 8, 8, 5))                          # مباني الفناء
    for s in (-1, 1):                                              # متاريس قدام البوابات
        out.append((0, s * (R + 9), 12, 2, 2.4))
        out.append((s * (R + 9), 0, 2, 12, 2.4))
    n = tries = 0
    size = cfg['size']
    while n < cfg['count'] and tries < 600:                        # صناديق برا القلعة
        tries += 1
        x, z = rng.uniform(-size + 5, size - 5), rng.uniform(-size + 5, size - 5)
        if max(abs(x), abs(z)) < R + 14:
            continue
        s = rng.uniform(2, 4)
        out.append((x, z, s, s, rng.choice([1.4, 2.2, 3.2])))
        n += 1
    for _ in range(8):                                             # صناديق صغيرة في الفناء
        x, z = rng.uniform(-24, 24), rng.uniform(-24, 24)
        if math.hypot(x, z) > 9 and max(abs(x), abs(z)) < 26 and min(abs(abs(x) - 16), abs(abs(z) - 16)) > 6:
            out.append((x, z, 2, 2, 1.4))
    return out


def gen_pyramids(cfg, rng):
    """أهرامات مدرجة (كل درجة 1.4م = ينفع تتنطط عليها) + أعمدة تغطية."""
    out = []
    for px, pz in cfg['pyr']:
        for base, h in ((18, 1.4), (12, 2.8), (6.5, 4.2)):
            out.append((px, pz, base, base, h))
    n = tries = 0
    size = cfg['size']
    while n < cfg['count'] and tries < 600:
        tries += 1
        x, z = rng.uniform(-size + 6, size - 6), rng.uniform(-size + 6, size - 6)
        if math.hypot(x, z) < 10 or any(math.hypot(x - px, z - pz) < 16 for px, pz in cfg['pyr']):
            continue
        out.append((x, z, rng.uniform(2, 4), rng.uniform(2, 4), rng.uniform(3, 7)))
        n += 1
    return out


def gen_labyrinth(cfg, rng):
    """متاهة DFS كبيرة + فتحات إضافية (braid) عشان فيه لفات ومش طرق مسدودة بس."""
    N, cs, th, H = cfg['cells'], cfg['cell'], 2.0, 6
    half = N // 2
    east = [[True] * N for _ in range(N)]    # east[i][j]: حيطة بين (i,j) و (i+1,j)
    north = [[True] * N for _ in range(N)]   # north[i][j]: حيطة بين (i,j) و (i,j+1)
    vis = [[False] * N for _ in range(N)]
    vis[half][half] = True
    stack = [(half, half)]
    while stack:
        i, j = stack[-1]
        nb = [(a, b) for a, b in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1))
              if 0 <= a < N and 0 <= b < N and not vis[a][b]]
        if not nb:
            stack.pop()
            continue
        a, b = rng.choice(nb)
        if a == i + 1:
            east[i][j] = False
        elif a == i - 1:
            east[a][j] = False
        elif b == j + 1:
            north[i][j] = False
        else:
            north[i][b] = False
        vis[a][b] = True
        stack.append((a, b))
    for i in range(N):
        for j in range(N):
            if i < N - 1 and east[i][j] and rng.random() < cfg['braid']:
                east[i][j] = False
            if j < N - 1 and north[i][j] and rng.random() < cfg['braid']:
                north[i][j] = False
    for k in (-1, 0):                         # منطقة البداية في النص مفتوحة
        east[half + k][half] = False
        north[half][half + k] = False
    for k in range(N):                        # الحدود برا (السور الخارجي بيتكفل بيها)
        east[N - 1][k] = False
        north[k][N - 1] = False
    out = []
    for i in range(N - 1):                    # حيطان رأسية: بنجمع المتتالي في بلوك واحد
        j = 0
        while j < N:
            if east[i][j]:
                j0 = j
                while j < N and east[i][j]:
                    j += 1
                out.append(((i - half) * cs + cs / 2, ((j0 + j - 1) / 2 - half) * cs,
                            th, (j - j0) * cs + th, H))
            else:
                j += 1
    for j in range(N - 1):                    # حيطان أفقية
        i = 0
        while i < N:
            if north[i][j]:
                i0 = i
                while i < N and north[i][j]:
                    i += 1
                out.append((((i0 + i - 1) / 2 - half) * cs, (j - half) * cs + cs / 2,
                            (i - i0) * cs + th, th, H))
            else:
                i += 1
    return out


def gen_city(cfg, rng):
    """شبكة مباني وشوارع + عربيات (صناديق واطية ينفع تتنطط عليها)."""
    out = []
    pitch, size, hmax = cfg['pitch'], cfg['size'], cfg['hmax']
    n = int((size - 6) // pitch)
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            if i == 0 and j == 0:             # ميدان في النص
                continue
            cx, cz = i * pitch, j * pitch
            bw, bd = rng.uniform(11, 16), rng.uniform(11, 16)
            if rng.random() < .3:             # بلوك مقسوم لمبنيين
                for s in (-1, 1):
                    out.append((cx + s * (bw / 4 + 1), cz, bw / 2 - 1.2, bd, rng.uniform(5, hmax)))
            else:
                out.append((cx, cz, bw, bd, rng.uniform(5, hmax)))
    for _ in range(18):
        lane = (rng.randint(-n, n - 1) + .5) * pitch
        along = rng.uniform(-size + 8, size - 8)
        x, z = (lane, along) if rng.random() < .5 else (along, lane)
        if math.hypot(x, z) < 9:
            continue
        horiz = rng.random() < .5
        out.append((x, z, 4 if horiz else 2, 2 if horiz else 4, 1.4))
    return out


def gen_canyon(cfg, rng):
    """سلاسل صخور طويلة على الطول + صخور مبعثرة."""
    out = []
    size = cfg['size']
    for x in (-72, -36, 36, 72):
        z = -size + 8
        while z < size - 16:
            L = min(rng.uniform(14, 28), size - 6 - z)
            if L < 8:
                break
            out.append((x + rng.uniform(-3, 3), z + L / 2, rng.uniform(4, 6), L, rng.uniform(5, 9)))
            z += L + rng.uniform(9, 14)
    n = tries = 0
    while n < cfg['count'] and tries < 600:
        tries += 1
        x, z = rng.uniform(-size + 6, size - 6), rng.uniform(-size + 6, size - 6)
        if math.hypot(x, z) < 12:
            continue
        out.append((x, z, rng.uniform(3, 6), rng.uniform(3, 6), rng.uniform(2, 5)))
        n += 1
    return out


GENS = {'random': gen_random, 'maze': gen_maze, 'platforms': gen_platforms, 'fortress': gen_fortress,
        'pyramids': gen_pyramids, 'labyrinth': gen_labyrinth, 'city': gen_city, 'canyon': gen_canyon}
GRID = {}
GRID_CELL = 8.0
pillar_boxes = []      # (x, z, نص العرض, نص العمق, ارتفاع القمة, دايري؟) - أسرع بكتير من قراءة خصائص الـ Entity
_MESH_EXT = {}


def _mesh_probe(kind):
    """بيجرب يعمل مجسم أسطوانة/مخروط جاهز من ursina ويقيس حجمه (لو مش موجود بنستخدم بدايله)."""
    if kind not in _MESH_EXT:
        try:
            m = Cylinder(14) if kind == 'cyl' else Cone(14)
            vs = [(v[0], v[1], v[2]) for v in m.vertices]
            ext = (min(v[0] for v in vs), max(v[0] for v in vs), min(v[1] for v in vs),
                   max(v[1] for v in vs), min(v[2] for v in vs), max(v[2] for v in vs))
            ok = len(vs) >= 12 and ext[1] - ext[0] > .1 and ext[3] - ext[2] > .1 and ext[5] - ext[4] > .1
            _MESH_EXT[kind] = ext if ok else None
        except Exception:
            _MESH_EXT[kind] = None
    return _MESH_EXT[kind]


def _mesh_entity(kind, cx, base_y, cz, w, h, d, col, collider=None):
    x0, x1, y0, y1, z0, z1 = _mesh_probe(kind)
    m = Cylinder(14) if kind == 'cyl' else Cone(14)
    sx, sy, sz = w / (x1 - x0), h / (y1 - y0), d / (z1 - z0)
    e = Entity(model=m, position=(cx - (x0 + x1) / 2 * sx, base_y - y0 * sy, cz - (z0 + z1) / 2 * sz),
               scale=(sx, sy, sz), color=col)
    if collider:
        e.collider = collider
    return e


def pick_shape(cfg, srng, sx, sz, h):
    shapes = cfg.get('shapes')
    if not shapes or Q()['simple_map'] or h < cfg.get('plain_below', 2.0):
        return 'box'
    k = srng.choice(shapes)
    asp = max(sx, sz) / max(.1, min(sx, sz))
    if k in ('round', 'boulder') and (asp > 1.6 or max(sx, sz) > 17):
        k = 'tower' if 'tower' in shapes else 'box'
    if k == 'tower' and h < 3.2:
        k = 'box'
    if k == 'round' and _mesh_probe('cyl') is None:
        k = 'tower' if h >= 3.2 else 'box'
    return k


def add_pillar(kind, x, z, sx, sz, h, col, srng):
    """بيبني شكل العمود (بصرياً) - التصادم دايماً بصندوق أو قطع ناقص بنفس المساحة."""
    dark, light = color.tint(col, -.22), color.tint(col, .15)
    rnd = False
    if kind == 'boulder':
        rnd = True
        main = Entity(model='sphere', position=(x, 0, z), scale=(sx, h * 2, sz), color=col, collider='box')
        world.append(main)
    elif kind == 'round':
        rnd = True
        main = _mesh_entity('cyl', x, 0, z, sx, h, sz, col, 'box')
        world.append(main)
        roof = srng.choice(['dome', 'cone', 'disc']) if h >= 3 else 'disc'
        if roof == 'cone' and _mesh_probe('cone') is None:
            roof = 'dome'
        if roof == 'dome':
            world.append(Entity(model='sphere', position=(x, h, z),
                                scale=(sx * 1.02, min(sx, sz) * .75, sz * 1.02), color=light))
        elif roof == 'cone':
            world.append(_mesh_entity('cone', x, h, z, sx * 1.18, max(1.6, min(sx, sz) * 1.0), sz * 1.18, dark))
        else:
            world.append(Entity(model='sphere', position=(x, h - .05, z),
                                scale=(sx * 1.08, .3, sz * 1.08), color=dark))
    else:
        main = Entity(model='cube', collider='box', position=(x, h / 2, z), scale=(sx, h, sz), color=col)
        world.append(main)
        if kind == 'tower':                                       # حزام علوي زي الشرفات + مبنى صغير فوق
            world.append(Entity(model='cube', position=(x, h - .3, z),
                                scale=(sx * 1.14, .6, sz * 1.14), color=dark))
            if h >= 7 and srng.random() < .6:
                world.append(Entity(model='cube', position=(x, h + .7, z),
                                    scale=(sx * .45, 1.4, sz * .45), color=light))
    pillars.append(main)
    box = (x, z, sx / 2, sz / 2, h, rnd)
    pillar_boxes.append(box)
    M = 2.5                                   # هامش (أكبر من نص قطر أي عدو/لاعب)
    for gi in range(int((x - sx / 2 - M) // GRID_CELL), int((x + sx / 2 + M) // GRID_CELL) + 1):
        for gj in range(int((z - sz / 2 - M) // GRID_CELL), int((z + sz / 2 + M) // GRID_CELL) + 1):
            GRID.setdefault((gi, gj), []).append(box)


def clear_world():
    for e in world:
        destroy(e)
    world.clear()
    pillars.clear()
    pillar_boxes.clear()
    GRID.clear()


def build_map(name):
    global ARENA
    cfg = MAPS[name]
    clear_world()
    ARENA = cfg['size']
    wh = cfg.get('wall_h', 8)
    window.color = C(cfg['sky'])
    scene.fog_color = C(cfg['sky'])
    apply_quality_view()
    world.append(Entity(model='plane', scale=ARENA * 2, color=C(cfg['ground']), collider='box'))
    for sx, sz, rx, rz in [(0, ARENA, ARENA * 2, 1), (0, -ARENA, ARENA * 2, 1),
                           (ARENA, 0, 1, ARENA * 2), (-ARENA, 0, 1, ARENA * 2)]:
        world.append(Entity(model='cube', position=(sx, wh / 2, sz), scale=(rx, wh, rz),
                            color=C(cfg['wall']), collider='box'))
    rng = random.Random(cfg['seed'])
    srng = random.Random(cfg['seed'] + 1)          # عشان الأشكال متغيرش الألوان
    for x, z, sx, sz, h in GENS[cfg['gen']](cfg, rng):
        col = C(rng.choice(cfg['pillars']))
        add_pillar(pick_shape(cfg, srng, sx, sz, h), x, z, sx, sz, h, col, srng)


def blocked(px, pz, feet, r):
    if abs(px) > ARENA - 1.3 or abs(pz) > ARENA - 1.3:
        return True
    for x, z, hx, hz, top, rnd in GRID.get((int(px // GRID_CELL), int(pz // GRID_CELL)), ()):
        if feet >= top - 0.3:
            continue
        dx, dz = abs(px - x), abs(pz - z)
        if rnd:
            if (dx / (hx + r)) ** 2 + (dz / (hz + r)) ** 2 < 1:
                return True
        elif dx < hx + r and dz < hz + r:
            return True
    return False


def ground_height(px, pz, feet, r):
    h = 0
    for x, z, hx, hz, top, rnd in GRID.get((int(px // GRID_CELL), int(pz // GRID_CELL)), ()):
        if feet < top - 0.6:
            continue
        dx, dz = abs(px - x), abs(pz - z)
        if rnd:
            if (dx / (hx + r * .5)) ** 2 + (dz / (hz + r * .5)) ** 2 < 1:
                h = max(h, top)
        elif dx < hx + r * .5 and dz < hz + r * .5:
            h = max(h, top)
    return h


# ================================================================ المهارات
SKILLS = [
    ('HEALTH',   '+20 max HP'),
    ('SHIELD',   '+20 max shield'),
    ('DAMAGE',   '+15% damage'),
    ('SPEED',    '+0.6 move speed'),
    ('RELOAD',   '-8% reload time'),
    ('HEADSHOT', '+25% headshot dmg'),
]
SKILL_ICON = {'HEALTH': 'heart', 'SHIELD': 'shield', 'DAMAGE': 'fist',
              'SPEED': 'speed', 'RELOAD': 'reload', 'HEADSHOT': 'head'}
MAX_LVL = 10
POINTS_PER_WAVE = 3

S = dict(ads_k=0.0, tp=True, shk_t=0.0, shk_m=0.0, cam_f=1.0, walk=0.0, state='menu', mode='WAVES', tier=0, timer=90.0, spawn_t=0.0, pm=False, set_from='menu', msg_id=0,
         hp=100, shield=50, score=0, wave=0, dash_cd=0.0, dead=False, paused=False,
         hurt_cd=0.0, kills=0, points=0, cd=0.0, reloading=False, reload_id=0, weapon=0,
         has_special=False, ads=False, fov_kick=0.0, hurt_flash=0.0, t=0.0, fps_acc=0.0, fps_n=0,
         lvl={n: 0 for n, _ in SKILLS}, cam_tick=99, cam_ray=1.0)


def lv(n):         return S['lvl'][n]
def max_hp():      return 100 + 20 * lv('HEALTH')
def max_shield():  return 50 + 20 * lv('SHIELD')
def dmg_mult():    return 1 + .15 * lv('DAMAGE')
def head_mult():   return 2 + .25 * lv('HEADSHOT')
def reload_mult(): return max(.3, 1 - .08 * lv('RELOAD'))
def move_speed():  return 9 + .6 * lv('SPEED')


def mode_has_skills():
    return S['mode'] in ('WAVES', 'SURVIVAL')


# ================================================================ الصوت (بيتولد بالكود كملفات WAV، من غير أي ملفات خارجية)
import wave
import struct
from panda3d.core import Filename

SFX_DIR = os.path.join(_BASE, 'flat_arena_sfx')
SR = 24000


def _noise(dur, f0, f1, decay, amp=1.0, delay=0.0):
    """ضوضاء بفلتر low-pass بيتحرك من f0 لـ f1 (الأساس لفرقعة الطلقة)."""
    n = int(SR * dur)
    out = [0.0] * int(SR * delay)
    y = 0.0
    rnd = random.random
    ratio = f1 / f0
    for i in range(n):
        t = i / SR
        fc = f0 * ratio ** (t / dur)
        y += (1 - math.exp(-6.2832 * fc / SR)) * ((rnd() * 2 - 1) - y)
        out.append(y * math.exp(-decay * t) * min(1.0, i / 12.0) * amp * 1.8)
    return out


def _tone(dur, f0, f1, decay, amp=1.0, kind='sine', delay=0.0):
    """نغمة بتنزل/تطلع في التردد (ثقل الطلقة)."""
    n = int(SR * dur)
    out = [0.0] * int(SR * delay)
    ph = 0.0
    ratio = f1 / f0
    for i in range(n):
        t = i / SR
        ph += f0 * ratio ** (t / dur) / SR
        p = ph % 1.0
        if kind == 'saw':
            v = 2 * p - 1
        elif kind == 'sq':
            v = 1.0 if p < .5 else -1.0
        elif kind == 'rich':
            v = math.sin(6.2832 * p) + .5 * math.sin(12.5664 * p) + .25 * math.sin(18.8496 * p)
        else:
            v = math.sin(6.2832 * p)
        out.append(v * math.exp(-decay * t) * min(1.0, i / 8.0) * amp)
    return out


def _mix(*layers):
    out = [0.0] * max(len(l) for l in layers)
    for l in layers:
        for i, v in enumerate(l):
            out[i] += v
    return out


def _echo(x, delay, fb, taps=3):
    d = int(SR * delay)
    out = list(x) + [0.0] * (d * taps)
    for k in range(1, taps + 1):
        g = fb ** k
        for i, v in enumerate(x):
            out[i + d * k] += v * g
    return out


def _write_wav(path, x, peak=.9):
    m = max(1e-6, max(abs(v) for v in x))
    k = peak / m
    nf = min(len(x), 240)
    data = bytearray()
    for i, v in enumerate(x):
        v = math.tanh(v * k * 1.15)
        if i >= len(x) - nf:
            v *= (len(x) - i) / nf
        data += struct.pack('<h', int(max(-1, min(1, v)) * 30000))
    with wave.open(path, 'wb') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(SR)
        f.writeframes(bytes(data))


def _arp(freqs, step, dur, decay, amp=.8, kind='rich'):
    return _mix(*[_tone(dur, f, f, decay, amp, kind, delay=i * step) for i, f in enumerate(freqs)])


SOUND_DEFS = {
    # --- صوت كل سلاح
    'shot_pistol': lambda: _echo(_mix(_noise(.2, 7500, 1200, 26), _tone(.16, 230, 70, 22, 1.0, 'rich'),
                                      _tone(.03, 1900, 900, 90, .5, 'sq')), .07, .25, 2),
    'shot_smg': lambda: _mix(_noise(.1, 6500, 1500, 48), _tone(.09, 320, 110, 45, .8, 'saw'),
                             _tone(.02, 2200, 1000, 120, .4)),
    'shot_shotgun': lambda: _echo(_mix(_noise(.5, 5000, 260, 9, 1.2), _tone(.4, 130, 40, 8, 1.1, 'rich'),
                                       _noise(.06, 9000, 3000, 70, .8)), .11, .3, 3),
    'shot_sniper': lambda: _echo(_mix(_noise(.3, 9000, 700, 16, 1.1), _tone(.7, 95, 28, 5, 1.2, 'rich'),
                                      _tone(.05, 2600, 900, 60, .6, 'sq')), .2, .35, 4),
    'shot_launcher': lambda: _echo(_mix(_tone(.55, 170, 42, 6, 1.2, 'rich'), _noise(.5, 300, 3200, 3.5, .5),
                                        _noise(.08, 5000, 1000, 40, .7)), .12, .25, 2),
    'shot_headhunter': lambda: _echo(_mix(_noise(.22, 8500, 1400, 22), _tone(.2, 420, 150, 20, 1.0, 'rich'),
                                          _tone(.6, 2600, 2550, 12, .16), _tone(.5, 3350, 3300, 14, .11),
                                          _tone(.04, 2000, 800, 80, .5, 'sq')), .09, .3, 3),
    'shot_m4': lambda: _mix(_noise(.13, 6800, 1700, 40), _tone(.11, 260, 95, 34, .9, 'saw'),
                            _tone(.025, 1700, 700, 100, .5, 'sq')),
    'shot_akm': lambda: _echo(_mix(_noise(.17, 5400, 900, 28, 1.15), _tone(.15, 185, 62, 24, 1.1, 'rich'),
                                   _tone(.03, 1400, 600, 90, .5, 'sq')), .05, .2, 2),
    'shot_minigun': lambda: _mix(_noise(.07, 5200, 1800, 60), _tone(.06, 215, 120, 55, .9, 'saw')),
    # --- أصوات الأسلحة التانية
    'pump': lambda: _mix(_noise(.04, 6000, 2000, 90, .8), _noise(.04, 4500, 1500, 90, .9, delay=.12),
                         _tone(.05, 300, 150, 60, .5, 'sq', delay=.12)),
    'bolt': lambda: _mix(_noise(.04, 5500, 1800, 90, .9), _tone(.05, 420, 200, 70, .5, 'sq'),
                         _noise(.05, 4500, 1200, 80, 1.0, delay=.16), _tone(.05, 300, 150, 70, .6, 'sq', delay=.16)),
    'mag_out': lambda: _mix(_noise(.05, 5000, 1500, 80), _tone(.05, 500, 250, 70, .5, 'sq')),
    'mag_in': lambda: _mix(_noise(.04, 6000, 2500, 90), _noise(.05, 4000, 1200, 70, .9, delay=.07),
                           _tone(.06, 380, 200, 60, .6, 'sq', delay=.07)),
    'empty': lambda: _mix(_noise(.03, 7000, 2500, 120), _tone(.03, 900, 600, 100, .3, 'sq')),
    'switch': lambda: _mix(_noise(.05, 3500, 900, 60, .8), _tone(.06, 500, 300, 50, .4)),
    # --- تأثيرات
    'boom': lambda: _echo(_mix(_noise(.9, 3000, 70, 3.5, 1.3), _tone(.7, 75, 22, 3.5, 1.3, 'rich'),
                               _noise(.1, 8000, 2000, 40, .8)), .15, .3, 3),
    'hit': lambda: _mix(_tone(.05, 1500, 900, 60, .6, 'sq'), _noise(.03, 6000, 3000, 100, .5)),
    'headshot': lambda: _mix(_tone(.18, 1500, 2100, 16, .7), _tone(.2, 2250, 3000, 14, .4, delay=.04),
                             _noise(.04, 8000, 3000, 80, .5)),
    'kill': lambda: _mix(_tone(.22, 300, 80, 14, 1.0, 'rich'), _noise(.16, 2500, 300, 16, .7)),
    'hurt': lambda: _mix(_tone(.28, 170, 55, 10, 1.1, 'saw'), _noise(.14, 1500, 200, 18, .8)),
    'dash': lambda: _noise(.25, 600, 7000, 8, .9),
    'jump': lambda: _tone(.15, 260, 560, 14, .8),
    'wave': lambda: _arp([392, 523, 659, 784], .1, .22, 9),
    'over': lambda: _arp([392, 330, 262, 196], .22, .4, 5, .7, 'saw'),
    'upgrade': lambda: _mix(_tone(.14, 600, 1200, 12, .7), _tone(.16, 900, 1500, 12, .6, delay=.08)),
    'special': lambda: _mix(_arp([523, 659, 784, 1047], .08, .3, 8), _tone(.5, 2600, 2600, 8, .15, delay=.2)),
}
SOUND_POOL = {'shot_minigun': 8, 'shot_smg': 6, 'shot_m4': 5, 'shot_akm': 5, 'shot_pistol': 3,
              'hit': 5, 'headshot': 3, 'kill': 4}
SHOT_SND = {'PISTOL': 'shot_pistol', 'SMG': 'shot_smg', 'SHOTGUN': 'shot_shotgun', 'SNIPER': 'shot_sniper',
            'LAUNCHER': 'shot_launcher', 'HEADHUNTER': 'shot_headhunter', 'M4': 'shot_m4', 'AKM': 'shot_akm',
            'MINIGUN': 'shot_minigun'}
SHOT_VOL = {'MINIGUN': .6, 'SMG': .75, 'M4': .8, 'SHOTGUN': 1.0, 'SNIPER': 1.0}
_SND = {}
_SIDX = {}


def _load_sfx():
    try:
        os.makedirs(SFX_DIR, exist_ok=True)
        fresh = [n for n in SOUND_DEFS if not os.path.exists(os.path.join(SFX_DIR, n + '.wav'))]
        if fresh:
            print(f'Generating {len(fresh)} sound effects (first run only)...')
        ldr = getattr(base, 'loader', None) or loader
        for name, fn in SOUND_DEFS.items():
            path = os.path.join(SFX_DIR, name + '.wav')
            if not os.path.exists(path):
                _write_wav(path, fn())
            fp = Filename.fromOsSpecific(path)
            _SND[name] = [ldr.loadSfx(fp) for _ in range(SOUND_POOL.get(name, 2))]
    except Exception as ex:
        print('Sound disabled:', ex)


def sfx(name, vol=1.0, rate=1.0):
    v = SET.get('volume', .8)
    pool = _SND.get(name)
    if v <= 0 or not pool:
        return
    i = _SIDX.get(name, 0)
    _SIDX[name] = (i + 1) % len(pool)
    try:
        snd = pool[i]
        snd.setVolume(max(0.0, min(1.0, vol * v)))
        snd.setPlayRate(rate)
        snd.play()
    except Exception:
        pass


def late_sfx(name, idx, delay, vol=1.0):
    """صوت متأخر (زي بامب الشوتجن) بيشتغل بس لو لسه ماسك نفس السلاح."""
    def go():
        if S['weapon'] == idx and not S['dead'] and S['state'] == 'play':
            sfx(name, vol)
    invoke(go, delay=delay)


_load_sfx()


# ================================================================ الأسلحة
# zoom = الـ FOV عند الضغط على كليك يمين (أقل = تكبير أكبر) ، scope = شاشة سكوب كاملة
WEAPONS = [
    dict(name='PISTOL',   dmg=1.3, rate=.28,  mag=12, reload=1.2, auto=False, pellets=1, spread=0,   pierce=1, blast=0, accent='#3a86ff', recoil=.15, zoom=70, scope=False),
    dict(name='SMG',      dmg=.7,  rate=.075, mag=35, reload=1.6, auto=True,  pellets=1, spread=1.6, pierce=1, blast=0, accent='#ff7096', recoil=.08, zoom=65, scope=False),
    dict(name='SHOTGUN',  dmg=.75, rate=.85,  mag=6,  reload=2.0, auto=False, pellets=9, spread=5.5, pierce=1, blast=0, accent='#fb8500', recoil=.45, zoom=75, scope=False),
    dict(name='SNIPER',   dmg=7.0, rate=1.2,  mag=5,  reload=2.2, auto=False, pellets=1, spread=0,   pierce=3, blast=0, accent='#7209b7', recoil=.5,  zoom=14, scope=True),
    dict(name='LAUNCHER', dmg=6.0, rate=1.5,  mag=3,  reload=2.4, auto=False, pellets=1, spread=0,   pierce=1, blast=6, accent='#e63946', recoil=.6,  zoom=70, scope=False),
    # ريفولفر: هيدشوت واحدة = موت فورى
    dict(name='HEADHUNTER', dmg=3.0, rate=.6, mag=6,  reload=2.4, auto=False, pellets=1, spread=0,   pierce=2, blast=0, accent='#c3ccd8', recoil=.45, zoom=50, scope=False, instakill=True),
    # ARs
    dict(name='M4',   dmg=1.0, rate=.095, mag=30, reload=1.8, auto=True, pellets=1, spread=.5, pierce=1, blast=0, accent='#2a9d8f', recoil=.1,  zoom=55, scope=False),
    dict(name='AKM',  dmg=1.7, rate=.115, mag=30, reload=2.0, auto=True, pellets=1, spread=.9, pierce=1, blast=0, accent='#6b705c', recoil=.16, zoom=55, scope=False),
    # ماشين جان: أسرع سلاح، 250 طلقة، وأعلى DPS في اللعبة (تقريبًا 31 ضرر/ثانية + بيخترق عدوين)
    dict(name='MINIGUN', dmg=1.1, rate=.035, mag=250, reload=3.5, auto=True, pellets=1, spread=2.2, pierce=2, blast=0, accent='#ff006e', recoil=.05, zoom=80, scope=False),
]
AMMO = [w['mag'] for w in WEAPONS]

# أيقونات الأسلحة (بتتولد بالكود)
GUNTEX = {w['name']: make_tex(gun_icon(w['name'], w['accent']), 'gun_' + w['name']) for w in WEAPONS}

# أجزاء السلاح اللي في الإيد: (الحجم، المكان، اللون[، دوران X])
#   a = لون السلاح   k = أسود   m = معدن فاتح   d = معدن غامق   g = ذهبي   w = خشب   l = عدسة زرقا   r = عدسة حمرا
PART_COL = {'k': INK, 'm': C('#8d99ae'), 'd': C('#5c677d'), 'g': GOLD,
            'w': C('#8d5524'), 'l': C('#4cc9f0'), 'r': C('#e63946'), 'x': C('#b07a45'),
            'z': C('#f4f7fb'), 'v': C('#b4becb'), 'h': C('#ffffff')}   # z/v/h = فضي لامع / فضي غامق / لمعة

GUN_SHAPES = {
    'PISTOL': [((.1, .1, .5), (0, 0, .1), 'a'), ((.1, .03, .5), (0, .06, .1), 'k'),
               ((.06, .06, .12), (0, 0, .42), 'd'), ((.09, .22, .14), (0, -.16, -.1), 'k'),
               ((.03, .04, .04), (0, .075, .32), 'k'), ((.04, .04, .04), (0, .075, -.12), 'k')],
    'SMG': [((.12, .16, .65), (0, 0, .05), 'a'), ((.06, .06, .3), (0, 0, .5), 'd'),
            ((.1, .1, .06), (0, 0, .67), 'k'), ((.07, .3, .1), (0, -.2, .12), 'k'),
            ((.08, .2, .1), (0, -.17, -.22), 'k'), ((.07, .1, .25), (0, .0, -.4), 'd'),
            ((.1, .05, .25), (0, .1, .05), 'k'), ((.07, .02, .12), (0, .13, .05), 'g')],
    'SHOTGUN': [((.15, .14, .5), (0, 0, 0), 'a'), ((.05, .05, .8), (0, .045, .5), 'm'),
                ((.05, .05, .8), (0, -.025, .5), 'd'), ((.12, .09, .3), (0, -.09, .4), 'w'),
                ((.1, .16, .4), (0, -.02, -.35), 'w'), ((.09, .12, .04), (0, .01, .9), 'k')],
    'SNIPER': [((.09, .11, 1.2), (0, 0, .25), 'a'), ((.04, .04, .6), (0, 0, 1.0), 'd'),
               ((.07, .07, .5), (0, .12, .15), 'k'), ((.09, .09, .04), (0, .12, .42), 'l'),
               ((.09, .09, .04), (0, .12, -.1), 'l'), ((.1, .18, .35), (0, -.04, -.5), 'k'),
               ((.03, .06, .04), (0, .07, .15), 'd')],
    'LAUNCHER': [((.2, .2, .9), (0, 0, .15), 'a'), ((.21, .21, .08), (0, 0, -.05), 'g'),
                 ((.21, .21, .08), (0, 0, .2), 'g'), ((.21, .21, .08), (0, 0, .45), 'g'),
                 ((.26, .26, .15), (0, 0, .65), 'k'), ((.15, .15, .02), (0, 0, .74), 'g'),
                 ((.08, .2, .1), (0, -.2, -.05), 'k'), ((.05, .08, .12), (0, .14, .1), 'l')],
    # ريفولفر فضي لامع: إطار + أسطوانة + ماسورة + قبضة خشب مايلة + هامر + شرايط لمعة
    'HEADHUNTER': [((.08, .11, .30), (0, 0, 0), 'a'),
                   ((.12, .14, .15), (0, .005, .10), 'z'),
                   ((.045, .05, .50), (0, .025, .45), 'v'),
                   ((.04, .035, .28), (0, -.025, .33), 'v'),
                   ((.03, .03, .03), (0, .06, .68), 'z'),
                   ((.07, .22, .10), (0, -.15, -.17), 'w', 15),
                   ((.035, .06, .05), (0, .085, -.15), 'v'),
                   ((.025, .05, .09), (0, -.065, -.02), 'k'),
                   ((.014, .012, .28), (0, .058, 0), 'h'),
                   ((.014, .012, .46), (0, .053, .45), 'h'),
                   ((.125, .012, .12), (0, .078, .10), 'h'),
                   ((.012, .10, .10), (.062, .005, .10), 'h')],
    'M4': [((.1, .13, .7), (0, 0, .05), 'a'),
           ((.095, .1, .5), (0, -.01, .62), 'k'),
           ((.035, .035, .35), (0, .01, .98), 'd'),
           ((.06, .06, .1), (0, .01, 1.16), 'k'),
           ((.05, .06, .5), (0, .1, .1), 'k'),
           ((.03, .07, .03), (0, .08, .9), 'k'),
           ((.07, .09, .06), (0, .06, .42), 'l'),
           ((.08, .12, .4), (0, -.02, -.45), 'k'),
           ((.07, .3, .12), (0, -.2, .12), 'd', 8),
           ((.07, .2, .1), (0, -.17, -.2), 'k', 15)],
    'AKM': [((.1, .13, .66), (0, 0, .05), 'a'),
            ((.1, .1, .45), (0, -.02, .62), 'w'),
            ((.07, .04, .35), (0, .06, .6), 'w'),
            ((.03, .03, .55), (0, .08, .78), 'm'),
            ((.035, .035, .4), (0, .01, 1.0), 'd'),
            ((.07, .07, .1), (0, .01, 1.2), 'k'),
            ((.03, .08, .03), (0, .075, 1.0), 'k'),
            ((.08, .14, .42), (0, -.04, -.45), 'w'),
            ((.07, .22, .12), (0, -.2, .1), 'd', 12),
            ((.07, .14, .12), (0, -.37, .2), 'd', 28),
            ((.07, .2, .1), (0, -.17, -.2), 'w', 15)],
    'MINIGUN': [((.2, .2, .5), (0, 0, 0), 'a'),
                ((.04, .04, .9), (0, .075, .65), 'm'), ((.04, .04, .9), (.065, .037, .65), 'd'),
                ((.04, .04, .9), (.065, -.037, .65), 'm'), ((.04, .04, .9), (0, -.075, .65), 'd'),
                ((.04, .04, .9), (-.065, -.037, .65), 'm'), ((.04, .04, .9), (-.065, .037, .65), 'd'),
                ((.22, .22, .06), (0, 0, 1.08), 'k'), ((.2, .2, .05), (0, 0, .6), 'k'),
                ((.2, .22, .3), (0, -.2, -.12), 'k'), ((.12, .03, .26), (0, -.2, -.12), 'g'),
                ((.06, .1, .3), (0, .16, .02), 'k'), ((.07, .2, .1), (0, -.17, -.3), 'k', 10)],
}
# مكان الإيدين (القبضة، والإيد الأمامية) ومكان وميض الفوهة
HANDS = {'PISTOL': [(0, -.1, -.1)], 'SMG': [(0, -.17, -.22), (0, -.06, .4)],
         'SHOTGUN': [(0, -.07, -.3), (0, -.09, .4)], 'SNIPER': [(0, -.12, -.3), (0, -.06, .5)],
         'LAUNCHER': [(0, -.19, -.05), (0, -.12, .45)], 'HEADHUNTER': [(0, -.2, -.2)],
         'M4': [(0, -.17, -.2), (0, -.07, .5)], 'AKM': [(0, -.17, -.2), (0, -.08, .55)],
         'MINIGUN': [(0, -.17, -.3), (0, -.12, .3)]}
MUZZLE = {'PISTOL': .5, 'SMG': .74, 'SHOTGUN': .95, 'SNIPER': 1.4, 'LAUNCHER': .85, 'HEADHUNTER': .72, 'M4': 1.22, 'AKM': 1.26, 'MINIGUN': 1.18}
SKIN = C('#ffcfa3')
SLEEVE = C('#ff7096')


def cur():
    return WEAPONS[S['weapon']]


def slots():
    if S['mode'] == 'ARMS RACE':
        return [ARMS_LADDER[S['tier']]]
    return sorted(CFG['loadout']) + ([SPECIAL] if S['has_special'] else [])


def available(i):
    return i in slots()


# ================================================================ اللاعب
class Player(Entity):
    def __init__(self):
        super().__init__(position=(0, 0, 0))
        self.radius = .6
        self.speed = 9
        self.vy = 0
        self.grounded = True
        self.dash_t = 0
        self.dash_dir = Vec3(0, 0, 0)
        self.pivot = Entity(parent=self, y=1.7)
        camera.parent = self.pivot
        camera.position = (0, 0, 0)
        camera.rotation = (0, 0, 0)
        camera.fov = SET['fov']

    def wish_dir(self):
        return (self.forward * (held_keys['w'] - held_keys['s']) +
                self.right * (held_keys['d'] - held_keys['a']))

    def try_move(self, dx, dz):
        nx, nz = self.x + dx, self.z + dz
        if not blocked(nx, self.z, self.y, self.radius):
            self.x = nx
        if not blocked(self.x, nz, self.y, self.radius):
            self.z = nz

    def start_dash(self):
        d = self.wish_dir()
        if d.length() == 0:
            d = self.forward
        self.dash_dir = d.normalized()
        self.dash_t = .18

    def input(self, key):
        if (key == 'space' and self.grounded and S['state'] == 'play' and not S['dead']
                and not S['paused'] and not S['pm']):
            self.vy = 10
            self.grounded = False
            sfx('jump', .6)

    def update(self):
        # حساسية الماوس (من الإعدادات) وبتقل وقت التكبير
        sens = 40 * SET['sens'] * clamp(camera.fov / SET['fov'], .12, 1)
        self.rotation_y += mouse.velocity[0] * sens
        self.pivot.rotation_x = clamp(self.pivot.rotation_x - mouse.velocity[1] * sens, -89, 89)
        self.speed = move_speed() * (.6 if S['ads'] else 1)
        w = self.wish_dir()
        if w.length() > 0:
            w = w.normalized() * self.speed * time.dt
            self.try_move(w.x, w.z)
        if self.dash_t > 0:
            self.dash_t -= time.dt
            self.try_move(self.dash_dir.x * 45 * time.dt, self.dash_dir.z * 45 * time.dt)
        self.vy -= 28 * time.dt
        self.y += self.vy * time.dt
        floor = ground_height(self.x, self.z, self.y, self.radius)
        if self.y <= floor:
            self.y = floor
            self.vy = 0
            self.grounded = True
        else:
            self.grounded = False


player = Player()

# ---------------------------------------------------------------- جسم اللاعب (بيظهر في منظور شخص ثالث)
body = Entity(parent=player)
head = Entity(parent=player.pivot)


def _bx(parent, pos, scl, col):
    return Entity(parent=parent, model='cube', position=pos, scale=scl, color=col)


_bx(body, (0, 1.2, 0), (.64, .74, .34), C('#3a86ff'))          # التيشيرت
_bx(body, (0, .84, 0), (.66, .12, .36), INK)                   # الحزام
_bx(body, (-.42, 1.38, 0), (.2, .22, .26), SLEEVE)             # الكتف الشمال
_bx(body, (.42, 1.38, 0), (.2, .22, .26), SLEEVE)              # الكتف اليمين
leg_l = Entity(parent=body, position=(-.16, .82, 0))
leg_r = Entity(parent=body, position=(.16, .82, 0))
for _lg in (leg_l, leg_r):
    _bx(_lg, (0, -.4, 0), (.28, .8, .3), C('#4361ee'))          # الرجل
    _bx(_lg, (0, -.75, .06), (.3, .14, .4), INK)                # الجزمة
_bx(head, (0, -.02, 0), (.4, .4, .4), SKIN)                    # الراس (بتلف لفوق وتحت مع الماوس)
_bx(head, (0, .2, -.02), (.43, .13, .44), INK)                 # الشعر
_bx(head, (-.1, .02, .205), (.07, .08, .02), INK)              # العيون
_bx(head, (.1, .02, .205), (.07, .08, .02), INK)

# السلاح متركب على "رِج" بيتحرك بين وضع الجنب (شخص ثالث) ووضع السكوب (قدام العين بالظبط)
gun_rig = Entity(parent=player.pivot)
gun = Entity(parent=gun_rig)
GUN_POS = Vec3(0, 0, 0)                  # مكان السلاح جوه الرِج (الارتداد بيتحرك منه ويرجعله)
TP_GUN = Vec3(.24, -.52, .5)             # مكان السلاح في الإيد - شخص ثالث (نسبة لراس اللاعب)
FP_GUN = Vec3(.4, -.32, .8)              # مكان السلاح - شخص أول
TP_CAM = Vec3(.8, .45, -3.7)             # الكاميرا ورا الكتف اليمين
# نقطة العين وقت السكوب بالنسبة لمركز السلاح: (الارتفاع فوق الماسورة، المسافة ورا السلاح)
# العين بتتحط على خط الشاخص/عدسة السكوب عشان المنظر يطلع من السلاح نفسه
ADS_EYE = {'PISTOL': (.10, -.45), 'SMG': (.16, -.60), 'SHOTGUN': (.14, -.55), 'SNIPER': (.12, -.38),
           'LAUNCHER': (.19, -.50), 'HEADHUNTER': (.13, -.45), 'M4': (.16, -.72), 'AKM': (.14, -.72),
           'MINIGUN': (.28, -.50)}
_body_vis = [None]


def set_body_visible(v):
    if _body_vis[0] != v:
        _body_vis[0] = v
        body.enabled = v
        head.enabled = v


def update_camera():
    """كاميرا شخص ثالث ورا الكتف + سكوب بيدخل ورا السلاح. بتتنادى كل فريم وقت اللعب."""
    dt = time.dt
    w = cur()
    S['ads_k'] += ((1.0 if S['ads'] else 0.0) - S['ads_k']) * min(1.0, 15 * dt)
    k = S['ads_k']
    ke = k * k * (3 - 2 * k)
    ey, ez = ADS_EYE[w['name']]
    hip = TP_GUN if S['tp'] else FP_GUN
    ads = Vec3(0, -ey, -ez)
    gun_rig.position = hip + (ads - hip) * ke
    cam = Vec3(0, 0, 0)
    dist = 0.0
    if S['tp']:
        piv = player.pivot
        o = piv.world_position
        wv = o + piv.right * TP_CAM.x + piv.up * TP_CAM.y + piv.forward * TP_CAM.z
        d = wv - o
        L = d.length()
        S['cam_tick'] += 1
        if S['cam_tick'] >= Q()['cam_every']:      # الـ raycast تقيل: بنعمله كل كام فريم حسب الجودة
            S['cam_tick'] = 0
            f = 1.0
            info = raycast(o, d / L, distance=L, ignore=[player] + enemies)
            if info.hit:
                f = max(.05, (info.distance - .4) / L)
            if wv.y < .4 < o.y:                    # ماتنزلش الكاميرا تحت الأرض
                f = min(f, max(.05, (o.y - .4) / (o.y - wv.y)))
            S['cam_ray'] = f
        f = S['cam_ray']
        if f < S['cam_f']:
            S['cam_f'] = f
        else:
            S['cam_f'] += (f - S['cam_f']) * min(1.0, 8 * dt)
        cam = TP_CAM * S['cam_f']
        dist = L * S['cam_f']
    cam = cam * (1 - ke)                           # وقت السكوب الكاميرا بترجع لعين اللاعب
    if S['shk_t'] > 0:
        S['shk_t'] -= dt
        m = S['shk_m'] * .06 * (1 - .6 * ke)
        cam = cam + Vec3(random.uniform(-m, m), random.uniform(-m, m), 0)
    else:
        S['shk_m'] = 0.0
    camera.position = cam
    set_body_visible(S['tp'] and dist > 1.3 and ke < .4)
    # حركة الرجلين
    moving = player.grounded and (held_keys['w'] or held_keys['s'] or held_keys['a'] or held_keys['d'])
    if moving:
        S['walk'] += dt * move_speed() * 1.1
    tgt = math.sin(S['walk']) * 35 if moving else 0
    leg_l.rotation_x += (tgt - leg_l.rotation_x) * min(1.0, 12 * dt)
    leg_r.rotation_x += (-tgt - leg_r.rotation_x) * min(1.0, 12 * dt)
flash_ent = None
shine_ent = None


def build_gun():
    global flash_ent, shine_ent
    shine_ent = None
    for c in list(gun.children):
        destroy(c)
    w = cur()
    name = w['name']
    for part in GUN_SHAPES[name]:
        scl, pos, cc = part[0], part[1], part[2]
        rot = part[3] if len(part) > 3 else 0
        col = C(w['accent']) if cc == 'a' else PART_COL[cc]
        Entity(parent=gun, model='cube', scale=scl, position=pos, color=col, rotation_x=rot)
    # الإيدين والكُم
    for hx, hy, hz in HANDS[name]:
        Entity(parent=gun, model='cube', scale=(.11, .11, .15), position=(hx, hy, hz), color=SKIN)
        Entity(parent=gun, model='cube', scale=(.14, .14, .45), position=(hx - .03, hy - .07, hz - .28),
               color=SLEEVE, rotation_x=-12)
    # وميض الفوهة
    flash_ent = Entity(parent=gun, model='quad', texture=T['flash'], position=(0, 0, MUZZLE[name]),
                       scale=.45, enabled=False)
    if name == 'HEADHUNTER':            # لمعة بتتحرك على الريفولفر الفضي
        shine_ent = Entity(parent=gun, position=(0, .1, .1))
        Entity(parent=shine_ent, model='cube', scale=(.12, .014, .014), color=color.white)
        Entity(parent=shine_ent, model='cube', scale=(.014, .12, .014), color=color.white)


def _off(e):
    try:
        e.enabled = False
    except Exception:
        pass


def muzzle_flash():
    if flash_ent is None:
        return
    flash_ent.rotation_z = random.uniform(0, 360)
    flash_ent.scale = random.uniform(.35, .55)
    flash_ent.enabled = True
    invoke(_off, flash_ent, delay=.05)


crosshair = Entity(parent=camera.ui, model='quad', texture=T['crosshair'], scale=.045)
hitm = Entity(parent=camera.ui, model='quad', texture=T['hitmark'], scale=.06, enabled=False)
kill_icon = Entity(parent=camera.ui, model='quad', texture=T['skull'], scale=.05, y=-.08, enabled=False)

# ---------------------------------------------------------------- شاشة السكوب (دايرة سودا حوالين الشاشة)
scope_ui = Entity(parent=camera.ui, enabled=False, z=1)
SCOPE_R = .43
for i in range(64):
    a = math.tau * i / 64
    d = SCOPE_R + .6
    Entity(parent=scope_ui, model='circle', color=color.black, scale=1.2,
           position=(math.cos(a) * d, math.sin(a) * d))
Entity(parent=scope_ui, model='quad', scale=(SCOPE_R * 2, .002), color=color.black)
Entity(parent=scope_ui, model='quad', scale=(.002, SCOPE_R * 2), color=color.black)
Entity(parent=scope_ui, model='quad', scale=.007, color=C('#e63946'))

# ---------------------------------------------------------------- الدم على الشاشة (فيجنيت + بقع)
vig = Entity(parent=camera.ui, model='quad', texture=T['vig'], scale=(window.aspect_ratio * 1.05, 1.05),
             z=.8, color=color.white, enabled=False)


def screen_blood(n=3):
    if not SET['blood']:
        return
    for _ in range(n):
        x = random.choice((-1, 1)) * random.uniform(.2, .75) * (window.aspect_ratio / 1.78)
        y = random.uniform(-.4, .4)
        s = random.uniform(.18, .38)
        sp = Entity(parent=camera.ui, model='quad', texture=T['splat%d' % random.randrange(3)],
                    position=(x, y, .5), scale=s, rotation_z=random.uniform(0, 360), color=color.white)
        sp.fade_out(value=0, duration=1.0, delay=.7)
        destroy(sp, delay=1.8)


# ================================================================ الواجهة داخل اللعبة (HUD بالأيقونات)
L = -.5 * window.aspect_ratio
R = -L
hud_root = Entity(parent=camera.ui)
_TC = {}


def settext(t, s):
    if _TC.get(id(t)) != s:
        t.text = s
        _TC[id(t)] = s


def ui(**kw):
    kw.setdefault('color', color.white)
    return Entity(parent=hud_root, model='quad', **kw)


def label(text, x, y, scale=1.1, col=None, origin=(-.5, 0)):
    return Text(parent=hud_root, text=text, position=(x, y), origin=origin, scale=scale,
                color=col or color.white)


class Bar:
    def __init__(self, x, y, w, h, col):
        self.w = w
        ui(origin=(-.5, 0), position=(x - .004, y, .3), scale=(w + .008, h + .008), color=INK)
        ui(origin=(-.5, 0), position=(x, y, .2), scale=(w, h), color=C('#4a4e69'))
        self.fill = ui(origin=(-.5, 0), position=(x, y, .1), scale=(w, h), color=col)
        self.txt = label('', x + w / 2, y, .8, origin=(0, 0))

    def set(self, ratio, text, col=None):
        self.fill.scale_x = max(.0001, self.w * clamp(ratio, 0, 1))
        settext(self.txt, text)
        if col is not None:
            self.fill.color = col


# --- يسار تحت: الصحة والدرع والداش
ui(texture=T['panel'], position=(L + .235, -.385, .5), scale=(.45, .2))
ui(texture=T['heart'], position=(L + .055, -.33), scale=.048)
ui(texture=T['shield'], position=(L + .055, -.385), scale=.048)
ui(texture=T['bolt'], position=(L + .055, -.44), scale=.048)
hp_bar = Bar(L + .095, -.33, .31, .032, C('#ff4d6d'))
sh_bar = Bar(L + .095, -.385, .31, .032, C('#4cc9f0'))
dash_bar = Bar(L + .095, -.44, .31, .032, GOLD)

# --- يمين تحت: كارت السلاح والذخيرة
ui(texture=T['panel'], position=(R - .235, -.385, .5), scale=(.45, .2))
card_icon = ui(texture=GUNTEX['PISTOL'], position=(R - .335, -.355), scale=(.2, .1))
card_name = label('', R - .335, -.44, .9, origin=(0, 0))
ui(texture=T['bullet'], position=(R - .205, -.325), scale=.05)
ammo_txt = label('', R - .175, -.325, 1.9)
pips = [ui(position=(R - .2 + k * .0165, -.42, 0), scale=(.011, .032), color=GOLD) for k in range(12)]
reload_txt = label('', R - .115, -.372, 1.0, col=GOLD, origin=(0, 0))

# --- فوق يسار: الموجة / القتلى / النقاط
chips = []
for k, (ic, y) in enumerate([('flag', .455), ('skull', .395), ('star', .335)]):
    ui(texture=T['panel'], position=(L + .17, y, .5), scale=(.3, .056))
    ui(texture=T[ic], position=(L + .045, y), scale=.042)
    chips.append(label('', L + .08, y, 1.15))
pts_bg = ui(texture=T['panel'], position=(L + .2, .275, .5), scale=(.36, .056), enabled=False)
pts_ic = ui(texture=T['plus'], position=(L + .045, .275), scale=.04, enabled=False)
pts_txt = label('', L + .08, .275, 1.0, col=GOLD)
pts_txt.enabled = False

# --- فوق في النص: الطور واسم الماب والصعوبة + معلومات الطور (وقت / سلاح جاي)
ui(texture=T['panel'], position=(0, .47, .5), scale=(.66, .05))
top_txt = label('', 0, .47, .95, origin=(0, 0))
mode_txt = label('', 0, .405, 1.5, origin=(0, 0))

# --- فوق يمين: FPS (بيتفعل من الإعدادات)
fps_txt = label('', R - .03, .42, .9, origin=(.5, 0))
fps_txt.enabled = False

# --- شريط الأسلحة (تحت في النص) بأيقونات وأرقام
slot_w = []
for k in range(4):
    bg = ui(texture=T['slot'], position=(0, -.43, .5), scale=(.15, .125), enabled=False)
    ic = ui(texture=GUNTEX['PISTOL'], position=(0, -.43), scale=(.125, .0625), enabled=False)
    num = label(str(k + 1), 0, -.4, 1.3, origin=(0, 0))
    num.enabled = False
    nm = label('', 0, -.468, .65, origin=(0, 0))
    nm.enabled = False
    slot_w.append((bg, ic, num, nm))

center_msg = Text(text='', origin=(0, 0), scale=2.5, color=C('#ff7096'), y=.15)
enemies = []
_HC = {}


def flash_msg(text, dur=3.5):
    """رسالة في نص الشاشة بتختفي بعد dur ثانية (من غير ما تمسح رسالة أحدث منها)."""
    S['msg_id'] += 1
    mid = S['msg_id']
    center_msg.text = text

    def clear():
        if S['msg_id'] == mid and not S['dead']:
            center_msg.text = ''
    invoke(clear, delay=dur)


def refresh_hud():
    w = cur()
    wi = S['weapon']
    m = S['mode']
    mh, ms = max_hp(), max_shield()
    hp_bar.set(S['hp'] / mh, f"{max(0, int(S['hp']))} / {mh}")
    sh_bar.set(S['shield'] / ms, f"{int(S['shield'])} / {ms}")
    ready = S['dash_cd'] <= 0
    dash_bar.set(1 - S['dash_cd'] / 2.5, 'READY' if ready else f"{S['dash_cd']:.1f}s",
                 GOLD if ready else C('#8d99ae'))
    settext(chips[0], f"{'WAVE' if m == 'WAVES' else 'LEVEL'}  {S['wave']}")
    settext(chips[1], f"KILLS  {S['kills']}")
    settext(chips[2], f"SCORE  {S['score']}")
    settext(top_txt, f"{m}  |  {MAP_NAMES[CFG['map']]}  |  {DIFF_NAMES[CFG['diff']]}")
    has_pts = S['points'] > 0
    pts_bg.enabled = pts_ic.enabled = pts_txt.enabled = has_pts
    if has_pts:
        settext(pts_txt, f"SKILL POINTS: {S['points']}  (TAB)")

    # معلومات الطور
    if m == 'ARMS RACE':
        ak = max(1, int(SET['arms_kills']))
        n = len(ARMS_LADDER)
        if S['tier'] < n - 1:
            need = ak * (S['tier'] + 1) - S['kills']
            txt = f"WEAPON {S['tier'] + 1}/{n}  -  NEXT IN {need} KILLS"
        else:
            txt = f"FINAL WEAPON  ({n}/{n})"
        mode_txt.color = GOLD
    elif m == 'TIME ATTACK':
        t = max(0, int(math.ceil(S['timer'])))
        txt = f"TIME  {t // 60}:{t % 60:02d}"
        mode_txt.color = C('#e63946') if t <= 10 else color.white
    elif m == 'SURVIVAL':
        txt = f"NEXT LEVEL IN {KILLS_PER_LEVEL - S['kills'] % KILLS_PER_LEVEL} KILLS"
        mode_txt.color = color.white
    else:
        txt = ''
    settext(mode_txt, txt)

    # كارت السلاح
    sl = tuple(slots())
    if _HC.get('w') != (wi, sl):
        _HC['w'] = (wi, sl)
        card_icon.texture = GUNTEX[w['name']]
        settext(card_name, w['name'])
        n = len(sl)
        for k, (bg, ic, num, nm) in enumerate(slot_w):
            on = k < n
            bg.enabled = ic.enabled = num.enabled = nm.enabled = on
            if not on:
                continue
            x = (k - (n - 1) / 2) * .165
            sel = sl[k] == wi
            bg.x, ic.x, num.x, nm.x = x, x, x - .055, x
            bg.texture = T['slot_sel'] if sel else T['slot']
            ic.texture = GUNTEX[WEAPONS[sl[k]]['name']]
            settext(nm, WEAPONS[sl[k]]['name'])
            nm.color = GOLD if sel else color.white
            num.color = GOLD if sel else color.white
    # الذخيرة
    ammo = AMMO[wi]
    key = (wi, ammo, S['reloading'])
    if _HC.get('a') != key:
        _HC['a'] = key
        settext(ammo_txt, f"{ammo} / {w['mag']}")
        settext(reload_txt, 'RELOADING' if S['reloading'] else '')
        for k, p in enumerate(pips):
            p.enabled = w['mag'] <= 12 and k < w['mag']
            p.color = GOLD if k < ammo else C('#4a4e69')


def popup(text, col, y=.1):
    t = Text(text=text, origin=(0, 0), position=(0, y), scale=1.6, color=col)
    t.animate_position((0, y + .08), duration=.5)
    destroy(t, delay=.5)


def set_play_ui(on):
    hud_root.enabled = on
    gun.enabled = on
    crosshair.enabled = on and SET['crosshair']
    if on:
        _HC.clear()
    else:
        scope_ui.enabled = False
        vig.enabled = False
        hitm.enabled = False
        kill_icon.enabled = False


# ---------------------------------------------------------------- قائمة المهارات (TAB)
panel = Entity(parent=camera.ui, enabled=False)
Entity(parent=panel, model='quad', scale=(.95, .85), color=C('#2b2d42ee'), z=1)
Text(parent=panel, text='SKILLS', origin=(0, 0), position=(0, .36), scale=2.4, color=C('#ffffff'))
points_label = Text(parent=panel, text='', origin=(0, 0), position=(0, .29), scale=1.4, color=GOLD)
Text(parent=panel, text='TAB = close', origin=(0, 0), position=(0, -.38), scale=1, color=C('#cdb4db'))
skill_labels = {}


def upgrade(name):
    if S['points'] <= 0 or S['lvl'][name] >= MAX_LVL:
        return
    S['points'] -= 1
    S['lvl'][name] += 1
    if name == 'HEALTH':
        S['hp'] = min(max_hp(), S['hp'] + 20)
    elif name == 'SHIELD':
        S['shield'] = min(max_shield(), S['shield'] + 20)
    refresh_skill_menu()


def refresh_skill_menu():
    points_label.text = f"Points: {S['points']}"
    for n, desc in SKILLS:
        skill_labels[n].text = f"{n:<9} Lv {S['lvl'][n]:>2}/{MAX_LVL}   {desc}"


for i, (n, desc) in enumerate(SKILLS):
    y = .19 - i * .092
    Entity(parent=panel, model='quad', texture=T[SKILL_ICON[n]], position=(-.43, y, -.1), scale=.06)
    skill_labels[n] = Text(parent=panel, text='', origin=(-.5, 0), position=(-.37, y), scale=1.15,
                           color=C('#ffffff'))
    b = Button(parent=panel, text='+', position=(.38, y), scale=(.07, .055), color=C('#ff7096'))
    b.on_click = (lambda nm=n: upgrade(nm))
refresh_skill_menu()


def toggle_skills():
    if S['dead'] or S['state'] != 'play' or S['pm']:
        return
    if not S['paused'] and not mode_has_skills():
        popup('NO SKILLS IN THIS MODE', GOLD)
        return
    S['paused'] = not S['paused']
    S['ads'] = False
    panel.enabled = S['paused']
    player.enabled = not S['paused']
    mouse.locked = not S['paused']
    crosshair.enabled = (not S['paused']) and SET['crosshair']
    if S['paused']:
        scope_ui.enabled = False
        gun.enabled = True
    refresh_skill_menu()


# ================================================================ معاينات المابات (صورة من فوق لكل ماب)
MAP_TEX = {}


def make_map_preview(name, px=256):
    """بيرسم الماب من فوق بنفس المولّد بتاع اللعبة (نفس الـ seed = نفس الشكل بالظبط)."""
    cfg = MAPS[name]
    size = cfg['size']
    im = Image.new('RGBA', (px, px), _hex(cfg['wall']))
    d = ImageDraw.Draw(im)
    m = 7
    d.rectangle([m, m, px - m, px - m], fill=_hex(cfg['ground']))
    k = (px - 2 * m) / (2.0 * size)
    crng = random.Random(1)
    edge = _hex('#2b2d42')
    for x, z, sx, sz, h in GENS[cfg['gen']](cfg, random.Random(cfg['seed'])):
        X, Y = px / 2 + x * k, px / 2 - z * k
        hw, hd = max(1.2, sx * k / 2), max(1.2, sz * k / 2)
        col = _shade(_hex(crng.choice(cfg["pillars"])), .78 + min(h, 12) / 12 * .3)
        d.rectangle([X - hw, Y - hd, X + hw, Y + hd], fill=col, outline=edge)
    d.ellipse([px / 2 - 5, px / 2 - 5, px / 2 + 5, px / 2 + 5], fill=_hex('#ffffff'), outline=edge, width=2)
    return im


for _mn in MAPS:
    MAP_TEX[_mn] = make_tex(make_map_preview(_mn), 'map_' + _mn)


# ================================================================ القائمة الرئيسية
menu = Entity(parent=camera.ui, enabled=True)
Entity(parent=menu, model='quad', scale=(2, 1.2), color=C('#2b2d42cc'), z=1)
Text(parent=menu, text='FLAT ARENA', origin=(0, 0), position=(0, .43), scale=4, color=C('#ffffff'))
btn_mode = Button(parent=menu, text='', position=(0, .325), scale=(.7, .07), color=C('#8338ec'))
mode_desc = Text(parent=menu, text='', origin=(0, 0), position=(0, .276), scale=1, color=C('#cdb4db'))
btn_map = Button(parent=menu, text='', position=(0, .21), scale=(.7, .07), color=C('#ff7096'))
map_thumb = Entity(parent=menu, model='quad', texture=MAP_TEX[MAP_NAMES[0]], position=(.45, .21, -.1), scale=(.1, .1))
map_desc = Text(parent=menu, text='', origin=(0, 0), position=(0, .162), scale=1, color=C('#cdb4db'))
btn_diff = Button(parent=menu, text='', position=(0, .095), scale=(.7, .07), color=C('#fb8500'))
btn_start_wave = Button(parent=menu, text='', position=(0, .015), scale=(.7, .07), color=C('#219ebc'))
loadout_label = Text(parent=menu, text='', origin=(0, 0), position=(0, -.055), scale=1.1,
                     color=C('#ffffff'))

# اختيار الأسلحة (بيختفي في ARMS RACE)
loadout_group = Entity(parent=menu)
weapon_btns = []
for k, i in enumerate(LOADOUT_IDS):
    x = (k - (len(LOADOUT_IDS) - 1) / 2) * .135
    wb = Button(parent=loadout_group, text='', position=(x, -.16), scale=(.127, .125), color=C('#3d405b'))
    Entity(parent=loadout_group, model='quad', texture=GUNTEX[WEAPONS[i]['name']], position=(x, -.142, -.1),
           scale=(.115, .058))
    lbl = Text(parent=loadout_group, text=WEAPONS[i]['name'], origin=(0, 0), position=(x, -.203), scale=.6,
               color=C('#ffffff'))
    lbl.z = -.2
    weapon_btns.append(wb)

# سلم الأسلحة (بيظهر في ARMS RACE بس)
ladder_group = Entity(parent=menu, enabled=False)
for k, wi in enumerate(ARMS_LADDER):
    x = (k - (len(ARMS_LADDER) - 1) / 2) * .125
    Entity(parent=ladder_group, model='quad', texture=GUNTEX[WEAPONS[wi]['name']], position=(x, -.14, -.1),
           scale=(.118, .059))
    Text(parent=ladder_group, text=f"{k + 1}.{WEAPONS[wi]['name']}", origin=(0, 0), position=(x, -.19),
         scale=.45, color=GOLD)

btn_play = Button(parent=menu, text='START', position=(0, -.30), scale=(.4, .1), color=C('#2a9d8f'))
btn_settings = Button(parent=menu, text='SETTINGS', position=(-.13, -.40), scale=(.22, .055),
                      color=C('#8d99ae'))
btn_quit = Button(parent=menu, text='QUIT', position=(.13, -.40), scale=(.2, .055), color=C('#6c757d'))
best_text = Text(parent=menu, text='', origin=(0, 0), position=(0, -.47), scale=1.1, color=GOLD)
Text(parent=menu, text='In game:  V = switch 1st / 3rd person view', origin=(0, 0), position=(0, -.53),
     scale=.9, color=C('#cdb4db'))


def refresh_main_menu():
    mode = MODES[CFG['mode']]
    name = MAP_NAMES[CFG['map']]
    btn_mode.text = f"MODE:  {mode}   (click to change)"
    mode_desc.text = MODE_DESC[mode]
    btn_map.text = f"MAP:  {name}   (click to choose)"
    map_thumb.texture = MAP_TEX[name]
    map_desc.text = f"{MAPS[name]['desc']}   -   {MAPS[name]['size'] * 2} x {MAPS[name]['size'] * 2} m"
    btn_diff.text = f"DIFFICULTY:  {DIFF_NAMES[CFG['diff']]}   (click to change)"
    btn_start_wave.text = f"START WAVE:  {START_WAVES[CFG['start']]}   (click to change)"
    btn_start_wave.enabled = (mode == 'WAVES')
    loadout_group.enabled = (mode != 'ARMS RACE')
    ladder_group.enabled = (mode == 'ARMS RACE')
    if mode == 'ARMS RACE':
        loadout_label.text = f"WEAPON LADDER  (every {int(SET['arms_kills'])} kills = next weapon)"
    else:
        loadout_label.text = 'LOADOUT (pick 1 to 3 weapons)'
    for k, wb in enumerate(weapon_btns):
        wb.color = C('#ff7096') if LOADOUT_IDS[k] in CFG['loadout'] else C('#3d405b')
    b = get_best()
    best_text.text = f"BEST ({mode} / {name} / {DIFF_NAMES[CFG['diff']]}):  {b['score']}  -  level {b['wave']}"


def cycle_mode():
    CFG['mode'] = (CFG['mode'] + 1) % len(MODES)
    refresh_main_menu()


def cycle_map():
    CFG['map'] = (CFG['map'] + 1) % len(MAP_NAMES)
    build_map(MAP_NAMES[CFG['map']])
    refresh_main_menu()


def cycle_diff():
    CFG['diff'] = (CFG['diff'] + 1) % len(DIFF_NAMES)
    refresh_main_menu()


def cycle_start():
    CFG['start'] = (CFG['start'] + 1) % len(START_WAVES)
    refresh_main_menu()


def toggle_loadout(i):
    lo = CFG['loadout']
    if i in lo:
        if len(lo) > 1:
            lo.remove(i)
    elif len(lo) < 3:
        lo.append(i)
    refresh_main_menu()


btn_mode.on_click = cycle_mode
btn_diff.on_click = cycle_diff
btn_start_wave.on_click = cycle_start
for i, wb in enumerate(weapon_btns):
    wb.on_click = (lambda k=i: toggle_loadout(LOADOUT_IDS[k]))
btn_quit.on_click = application.quit

# ================================================================ شاشة اختيار الماب (كروت بصور)
map_panel = Entity(parent=camera.ui, enabled=False)
Entity(parent=map_panel, model='quad', scale=(2, 1.2), color=C('#2b2d42f2'), z=1)
Text(parent=map_panel, text='CHOOSE MAP', origin=(0, 0), position=(0, .43), scale=2.4, color=C('#ffffff'))
map_cards = []
_COLS = 5


def _card_pos(i):
    c, r = i % _COLS, i // _COLS
    return (c - (_COLS - 1) / 2) * .30, .2 - r * .38


for _i, _mn in enumerate(MAP_NAMES):
    _x, _y = _card_pos(_i)
    _b = Button(parent=map_panel, text='', position=(_x, _y), scale=(.27, .34), color=C('#3d405b'))
    Entity(parent=map_panel, model='quad', texture=MAP_TEX[_mn], position=(_x, _y + .045, -.1), scale=(.23, .23))
    Text(parent=map_panel, text=_mn, origin=(0, 0), position=(_x, _y - .098, -.2), scale=.9, color=C('#ffffff'))
    Text(parent=map_panel, text=f"{MAPS[_mn]['size'] * 2}x{MAPS[_mn]['size'] * 2} m", origin=(0, 0),
         position=(_x, _y - .135, -.2), scale=.65, color=C('#cdb4db'))
    _b.on_click = (lambda k=_i: select_map(k))
    map_cards.append(_b)
map_info = Text(parent=map_panel, text='', origin=(0, 0), position=(0, -.38), scale=1.1, color=GOLD)
btn_map_back = Button(parent=map_panel, text='BACK', position=(0, -.45), scale=(.25, .05), color=C('#6c757d'))


def refresh_map_picker():
    for k, b in enumerate(map_cards):
        b.color = C('#ffb703') if k == CFG['map'] else C('#3d405b')
    n = MAP_NAMES[CFG['map']]
    map_info.text = f"{n}: {MAPS[n]['desc']}"


def open_map_picker():
    refresh_map_picker()
    menu.enabled = False
    map_panel.enabled = True


def close_map_picker():
    map_panel.enabled = False
    menu.enabled = True
    refresh_main_menu()


def select_map(k):
    CFG['map'] = k
    build_map(MAP_NAMES[k])
    close_map_picker()


btn_map.on_click = open_map_picker
btn_map_back.on_click = close_map_picker


# ================================================================ قائمة الإعدادات
SETTING_ROWS = [
    dict(k='quality', label='Graphics (weak PC = LOW)', t='num', lo=0, hi=2, step=1, fmt='{:.0f}',
         names=QUALITY_NAMES),
    dict(k='sens', label='Mouse sensitivity', t='num', lo=.2, hi=3.0, step=.1, fmt='{:.1f}'),
    dict(k='fov', label='Field of view', t='num', lo=60, hi=120, step=5, fmt='{:.0f}'),
    dict(k='aim_toggle', label='Aim mode', t='bool', names=('HOLD', 'TOGGLE')),
    dict(k='crosshair', label='Crosshair', t='bool', names=('OFF', 'ON')),
    dict(k='shake', label='Screen shake', t='bool', names=('OFF', 'ON')),
    dict(k='blood', label='Blood effects', t='bool', names=('OFF', 'ON')),
    dict(k='vignette', label='Damage vignette', t='bool', names=('OFF', 'ON')),
    dict(k='show_fps', label='Show FPS', t='bool', names=('OFF', 'ON')),
    dict(k='auto_reload', label='Auto reload', t='bool', names=('OFF', 'ON')),
    dict(k='enemy_amt', label='Enemy amount', t='num', lo=.5, hi=2.5, step=.25, fmt='x{:.2f}'),
    dict(k='enemy_spd', label='Enemy speed', t='num', lo=.5, hi=1.8, step=.1, fmt='x{:.1f}'),
    dict(k='dmg_taken', label='Damage taken', t='num', lo=.25, hi=3.0, step=.25, fmt='x{:.2f}'),
    dict(k='special_chance', label='Special weapon %', t='num', lo=0, hi=100, step=5, fmt='{:.0f}%'),
    dict(k='arms_kills', label='Arms race kills', t='num', lo=2, hi=10, step=1, fmt='{:.0f}'),
    dict(k='time_limit', label='Time attack secs', t='num', lo=30, hi=300, step=15, fmt='{:.0f}'),
    dict(k='volume', label='Sound volume', t='num', lo=0, hi=1, step=.1, fmt='{:.0%}'),
]

settings_panel = Entity(parent=camera.ui, enabled=False)
Entity(parent=settings_panel, model='quad', scale=(1.5, .95), color=C('#2b2d42f2'), z=1)
Text(parent=settings_panel, text='SETTINGS', origin=(0, 0), position=(0, .41), scale=2.4, color=C('#ffffff'))
set_widgets = {}


def apply_quality_view():
    q = Q()
    camera.clip_plane_far = q['far']
    if q['fog'] is None:
        scene.fog_density = (ARENA * 1.2, ARENA * 3.2)
    else:
        scene.fog_density = q['fog']


def apply_settings():
    camera.fov = SET['fov']
    apply_quality_view()
    fps_txt.enabled = SET['show_fps']
    for nm in ('fps_counter', 'entity_counter', 'collider_counter'):    # عدادات ursina الافتراضية
        try:
            getattr(window, nm).enabled = False
        except Exception:
            pass


def refresh_settings():
    for row in SETTING_ROWS:
        w = set_widgets[row['k']]
        if row['t'] == 'bool':
            on = bool(SET[row['k']])
            w.text = row['names'][int(on)]
            w.color = C('#2a9d8f') if on else C('#6c757d')
        else:
            w.text = (row['names'][int(SET[row['k']])] if 'names' in row
                      else row['fmt'].format(SET[row['k']]))


def set_change(row, d):
    k = row['k']
    if row['t'] == 'bool':
        SET[k] = not SET[k]
    else:
        SET[k] = round(clamp(SET[k] + d * row['step'], row['lo'], row['hi']), 3)
    save_settings()
    refresh_settings()
    apply_settings()


def reset_settings():
    SET.clear()
    SET.update(SET_DEFAULT)
    save_settings()
    refresh_settings()
    apply_settings()


for idx, row in enumerate(SETTING_ROWS):
    col, r = divmod(idx, 9)
    x0 = -.72 + col * .74
    y = .30 - r * .07
    Text(parent=settings_panel, text=row['label'], origin=(-.5, 0), position=(x0, y), scale=1.0,
         color=C('#ffffff'))
    if row['t'] == 'bool':
        wd = Button(parent=settings_panel, text='', position=(x0 + .585, y), scale=(.19, .052),
                    color=C('#6c757d'))
        wd.on_click = (lambda rw=row: set_change(rw, 0))
    else:
        bm = Button(parent=settings_panel, text='-', position=(x0 + .5, y), scale=(.045, .05),
                    color=C('#ff7096'))
        bm.on_click = (lambda rw=row: set_change(rw, -1))
        wd = Text(parent=settings_panel, text='', origin=(0, 0), position=(x0 + .585, y), scale=1.0,
                  color=GOLD)
        bp = Button(parent=settings_panel, text='+', position=(x0 + .67, y), scale=(.045, .05),
                    color=C('#ff7096'))
        bp.on_click = (lambda rw=row: set_change(rw, 1))
    set_widgets[row['k']] = wd

btn_set_reset = Button(parent=settings_panel, text='RESET DEFAULTS', position=(-.2, -.33), scale=(.3, .06),
                       color=C('#fb8500'))
btn_set_back = Button(parent=settings_panel, text='BACK', position=(.2, -.33), scale=(.3, .06),
                      color=C('#2a9d8f'))
Text(parent=settings_panel, text='Settings are saved automatically', origin=(0, 0), position=(0, -.42),
     scale=.9, color=C('#cdb4db'))
refresh_settings()


def open_settings(src):
    S['set_from'] = src
    refresh_settings()
    if src == 'menu':
        menu.enabled = False
    else:
        pause_menu.enabled = False
    settings_panel.enabled = True


def close_settings():
    settings_panel.enabled = False
    apply_settings()
    if S['set_from'] == 'menu':
        menu.enabled = True
        refresh_main_menu()
    else:
        pause_menu.enabled = True


btn_set_reset.on_click = reset_settings
btn_set_back.on_click = close_settings
btn_settings.on_click = (lambda: open_settings('menu'))


# ================================================================ قائمة الإيقاف (Esc)
pause_menu = Entity(parent=camera.ui, enabled=False)
Entity(parent=pause_menu, model='quad', scale=(2, 1.2), color=C('#2b2d42c0'), z=1)
Text(parent=pause_menu, text='PAUSED', origin=(0, 0), position=(0, .32), scale=3.5, color=C('#ffffff'))
pause_info = Text(parent=pause_menu, text='', origin=(0, 0), position=(0, .23), scale=1.3, color=GOLD)
btn_resume = Button(parent=pause_menu, text='RESUME', position=(0, .12), scale=(.5, .085), color=C('#2a9d8f'))
btn_restart = Button(parent=pause_menu, text='RESTART', position=(0, .01), scale=(.5, .085), color=C('#fb8500'))
btn_pset = Button(parent=pause_menu, text='SETTINGS', position=(0, -.10), scale=(.5, .085), color=C('#219ebc'))
btn_pexit = Button(parent=pause_menu, text='EXIT TO MAIN MENU', position=(0, -.21), scale=(.5, .085),
                   color=C('#e63946'))
Text(parent=pause_menu, text='ESC = resume', origin=(0, 0), position=(0, -.32), scale=1, color=C('#cdb4db'))
Text(parent=pause_menu, text='V (in game) = switch 1st / 3rd person view', origin=(0, 0), position=(0, -.37),
     scale=.9, color=C('#cdb4db'))


def open_pause():
    if S['state'] != 'play' or S['dead'] or S['pm']:
        return
    S['pm'] = True
    S['ads'] = False
    scope_ui.enabled = False
    hud_root.enabled = False
    gun.enabled = True
    crosshair.enabled = False
    player.enabled = False
    mouse.locked = False
    camera.fov = SET['fov']
    pause_info.text = f"{S['mode']}  -  SCORE {S['score']}  -  KILLS {S['kills']}"
    pause_menu.enabled = True


def close_pause():
    S['pm'] = False
    pause_menu.enabled = False
    settings_panel.enabled = False
    hud_root.enabled = True
    _HC.clear()
    player.enabled = True
    mouse.locked = True
    crosshair.enabled = SET['crosshair']


def restart_run():
    if S['state'] == 'play' and not S['dead']:
        save_best(S['score'], S['wave'])
    new_run()


btn_resume.on_click = close_pause
btn_restart.on_click = restart_run
btn_pset.on_click = (lambda: open_settings('pause'))
btn_pexit.on_click = (lambda: show_menu())


def close_overlays():
    pause_menu.enabled = False
    settings_panel.enabled = False
    panel.enabled = False


def clear_decals():
    for d in DECALS:
        destroy(d)
    DECALS.clear()


def show_menu():
    if S['state'] == 'play' and not S['dead']:
        save_best(S['score'], S['wave'])
    close_overlays()
    S['state'] = 'menu'
    S['dead'] = False
    S['paused'] = False
    S['pm'] = False
    S['ads'] = False
    for e in enemies[:]:
        destroy(e)
    enemies.clear()
    clear_decals()
    player.enabled = False
    mouse.locked = False
    camera.fov = SET['fov']
    center_msg.text = ''
    camera.position = (0, 0, 0)
    set_body_visible(False)
    set_play_ui(False)
    menu.enabled = True
    refresh_main_menu()


# ================================================================ الدم والتأثيرات
def blood_burst(pos, n=8, power=1.0):
    if not SET['blood']:
        return
    for _ in range(max(1, int(n * Q()['fx']))):
        b = Entity(model='cube', position=pos, scale=random.uniform(.08, .16), color=random.choice(BLOOD_COLS))
        tgt = pos + Vec3(random.uniform(-1.4, 1.4) * power, random.uniform(-.2, 1.6) * power,
                         random.uniform(-1.4, 1.4) * power)
        b.animate_position(tgt, duration=.35, curve=curve.out_expo)
        b.animate_y(.05, duration=.45, delay=.3, curve=curve.in_quad)
        b.animate_scale(0, duration=.25, delay=.6)
        destroy(b, delay=.9)


def floor_splat(x, z, size=1.8):
    if not SET['blood']:
        return
    d = Entity(model='quad', texture=T['splat%d' % random.randrange(3)], position=(x, .03, z),
               rotation=(90, 0, random.uniform(0, 360)), scale=size, color=C('#ffffffdd'))
    DECALS.append(d)
    if len(DECALS) > Q()['decals']:
        destroy(DECALS.pop(0))


def kill_flash():
    kill_icon.enabled = True
    invoke(_off, kill_icon, delay=.4)


# ================================================================ الأعداء
KINDS = {
    #           hp   speed size  dmg  color        points
    'grunt':  ( 3,   4.5,  1.0,  8,  C('#ffffff'),  10),
    'runner': ( 2,   8.5,  0.85, 5,  C('#ff4d6d'),  15),
    'tank':   (14,   2.6,  1.6, 20,  C('#7b2cbf'),  50),
}


def safe_spawn(rmin, rmax, r):
    """مكان ظهور سليم: مش جوه عمود ومش قريب من اللاعب."""
    rmax = max(rmin + 1, rmax)
    for _ in range(80):
        ang = random.uniform(0, math.tau)
        rad = random.uniform(rmin, rmax)
        x, z = math.cos(ang) * rad, math.sin(ang) * rad
        if not blocked(x, z, 0, r + .5) and math.hypot(x - player.x, z - player.z) > 12:
            return x, z
    return ARENA - 4, ARENA - 4


class Enemy(Entity):
    def __init__(self, kind, wave, **kw):
        hp, spd, size, dmg, col, pts = KINDS[kind]
        super().__init__(scale=size, **kw)
        self.collider = BoxCollider(self, center=Vec3(0, .9, 0), size=Vec3(.9, 1.8, .9))
        d = D()
        self.kind = kind
        self.base_color = col
        self.hp = (hp + wave // 3) * d['hp']
        self.speed = spd * (1 + wave * 0.05) * d['spd'] * SET['enemy_spd']
        self.dmg = max(1, int(dmg * d['dmg']))
        self.pts = pts
        self.walk = random.uniform(0, 6)
        self.slide_dir = random.choice((1, -1))
        self.stuck_t = 0.0
        self.last = Vec3(self.x, 0, self.z)
        self.fx, self.fz = self.x, self.z      # نسخة رقمية من المكان (أسرع من خصائص الـ Entity)
        self.back_t = 0.0                      # وقت التراجع بعد ما يضرب
        dark = color.tint(col, -.25)
        self.parts = []

        def part(parent, pos, scl, c):
            e = Entity(parent=parent, model='cube', position=pos, scale=scl, color=c)
            self.parts.append((e, c))
            return e

        self.detail = Q()['detail']
        part(self, (0, 1.05, 0), (.6, .7, .35), col)
        part(self, (0, 1.65, 0), (.42, .42, .42), col)
        if self.detail:                                  # في LOW: جسم + راس بس (أسرع بكتير)
            part(self, (.3, 1.1, .3), (.12, .12, .5), INK)
            self.leg_l = Entity(parent=self, position=(-.15, .7, 0))
            self.leg_r = Entity(parent=self, position=(.15, .7, 0))
            part(self.leg_l, (0, -.35, 0), (.26, .7, .28), dark)
            part(self.leg_r, (0, -.35, 0), (.26, .7, .28), dark)
            self.arm_l = Entity(parent=self, position=(-.42, 1.35, 0))
            self.arm_r = Entity(parent=self, position=(.42, 1.35, 0))
            part(self.arm_l, (0, -.3, 0), (.2, .6, .22), col)
            part(self.arm_r, (0, -.3, 0), (.2, .6, .22), col)

    def relocate(self):
        x, z = safe_spawn(min(ARENA * .4, 40), min(ARENA - 4, 90), self.scale_x * .45)
        self.x, self.z = x, z
        self.fx, self.fz = x, z
        self.last = Vec3(x, 0, z)
        self.stuck_t = 0

    def steer(self, step):
        r = self.scale_x * .45
        nx, nz = self.x + step.x, self.z + step.z
        if not blocked(nx, nz, 0, r):
            self.x, self.z = nx, nz
        elif not blocked(nx, self.z, 0, r):
            self.x = nx
        elif not blocked(self.x, nz, 0, r):
            self.z = nz
        else:
            tx, tz = -step.z * self.slide_dir, step.x * self.slide_dir
            if not blocked(self.x + tx, self.z + tz, 0, r):
                self.x += tx
                self.z += tz
        self.fx, self.fz = self.x, self.z

    def update(self):
        if S['state'] != 'play' or S['dead'] or S['paused'] or S['pm']:
            return
        # حماية: لو العدو جوه عمود أو عالق، ننقله لمكان سليم (عشان مايختفيش والموجة تخلص)
        if blocked(self.x, self.z, 0, self.scale_x * .45):
            self.relocate()
        d = Vec3(player.x - self.x, 0, player.z - self.z)
        dist = d.length()
        self.stuck_t += time.dt
        if self.stuck_t > 2.5:
            if distance(Vec3(self.x, 0, self.z), self.last) < .6 and dist > 8:
                self.relocate()
            self.last = Vec3(self.x, 0, self.z)
            self.stuck_t = 0
        keep = self.scale_x * .45 + 1.6           # أقرب مسافة يقف عندها من اللاعب (كبّرناها عشان مايظهروش لازقين في الكاميرا)
        if dist > 0.01:
            dn = d / dist
            if self.back_t > 0:                    # بعد الضربة يتراجع شوية بدل ما يفضل لازق
                self.back_t -= time.dt
                self.steer(dn * (-self.speed * .8 * time.dt))
            elif dist > keep:
                self.steer(dn * min(self.speed * time.dt, dist - keep + .05))
            elif dist < keep - .35:               # لو دخل في اللاعب يتزحزح لبره
                self.steer(dn * (-self.speed * 1.2 * time.dt))
        # مايتكدسوش فوق بعض
        px = pz = 0.0
        for o in enemies:
            if o is self:
                continue
            ddx, ddz = self.fx - o.fx, self.fz - o.fz
            m = (self.scale_x + o.scale_x) * .45 + .2
            d2 = ddx * ddx + ddz * ddz
            if d2 < m * m:
                dd = math.sqrt(d2) or .01
                push = (m - dd) / m
                px += ddx / dd * push
                pz += ddz / dd * push
        if px or pz:
            self.steer(Vec3(px, 0, pz) * (self.speed * .9 * time.dt))
        self.look_at_2d(player.position, 'y')
        if self.detail:
            self.walk += time.dt * self.speed * 1.4
            sw = math.sin(self.walk) * 35
            self.leg_l.rotation_x = sw
            self.leg_r.rotation_x = -sw
            self.arm_l.rotation_x = -sw * .6
        if dist < keep + .5 and S['hurt_cd'] <= 0:
            hurt(self.dmg)
            self.back_t = .6        # بعد الضربة يبعد ويلف قبل ما يهاجم تاني

    def unflash(self):
        if self.hp > 0:
            for e, c in self.parts:
                e.color = c

    def hit(self, damage, head=False):
        if self.hp <= 0:
            return
        self.hp -= damage
        for e, _ in self.parts:
            e.color = FLASH
        invoke(self.unflash, delay=.07)
        chest = self.world_position + Vec3(0, (1.6 if head else 1.1) * self.scale_y, 0)
        if self.hp <= 0:
            bonus = 5 if head else 0
            S['score'] += int((self.pts + bonus) * D()['score'])
            S['kills'] += 1
            explode(self.world_position + Vec3(0, .9 * self.scale_y, 0), self.base_color)
            blood_burst(chest, 16, 1.5)
            floor_splat(self.x, self.z, random.uniform(1.5, 2.4) * max(1, self.scale_x))
            kill_flash()
            if self in enemies:
                enemies.remove(self)
            destroy(self)
            sfx('kill')
            on_kill()
        else:
            blood_burst(chest, 3, .7)


def explode(pos, col, n=10):
    for _ in range(max(2, int(n * Q()['fx']))):
        b = Entity(model='cube', position=pos, scale=.22, color=col)
        b.animate_position(pos + Vec3(random.uniform(-2, 2), random.uniform(.5, 3),
                                      random.uniform(-2, 2)),
                           duration=.5, curve=curve.out_expo)
        b.animate_scale(0, duration=.5)
        destroy(b, delay=.55)


def pick_kind(w):
    roll = random.random()
    if w >= 3 and roll < 0.2:
        return 'tank'
    if w >= 2 and roll < 0.5:
        return 'runner'
    return 'grunt'


def spawn_enemy(w):
    kind = pick_kind(w)
    x, z = safe_spawn(min(ARENA * .5, 45), min(ARENA - 4, 90), KINDS[kind][2] * .45)
    enemies.append(Enemy(kind, w, position=(x, 0, z)))


def maybe_special():
    """فرصة (من الإعدادات، الافتراضي 30%) إنك تاخد سلاح HEADHUNTER الخاص."""
    if S['has_special'] or S['mode'] not in ('WAVES', 'SURVIVAL'):
        return ''
    if random.random() * 100 < SET['special_chance']:
        S['has_special'] = True
        sfx('special')
        return '\nSPECIAL WEAPON: HEADHUNTER REVOLVER!\nHEADSHOT = INSTANT KILL'
    return ''


def spawn_wave():
    S['wave'] += 1
    w = S['wave']
    msg = f'WAVE {w}'
    if w > START_WAVES[CFG['start']]:
        S['points'] += POINTS_PER_WAVE
        msg += f'\n+{POINTS_PER_WAVE} SKILL POINTS (TAB)'
        refresh_skill_menu()
        msg += maybe_special()
    flash_msg(msg, 3.5)
    sfx('wave')
    n = min(Q()['max_en'], max(3, int((4 + w * 2) * D()['cnt'] * SET['enemy_amt'])))
    for _ in range(n):
        spawn_enemy(w)
    S['hp'] = min(max_hp(), S['hp'] + 20)
    S['shield'] = min(max_shield(), S['shield'] + 25)


# ---------------------------------------------------------------- الأطوار المستمرة (ARMS RACE / SURVIVAL / TIME ATTACK)
def cont_params():
    k = S['kills']
    cnt = D()['cnt'] * SET['enemy_amt']
    base = 9 if S['mode'] == 'TIME ATTACK' else 6
    cap = max(3, int(min(Q()['max_en'], (base + k * .3) * cnt)))
    interval = max(.35, (2.0 - k * .025) / max(.5, cnt))
    if S['mode'] == 'TIME ATTACK':
        interval *= .75
    return cap, interval


def continuous_update():
    S['spawn_t'] -= time.dt
    if S['spawn_t'] <= 0:
        cap, interval = cont_params()
        S['spawn_t'] = interval
        if len(enemies) < cap:
            spawn_enemy(S['wave'])


def arms_upgrade():
    idx = ARMS_LADDER[S['tier']]
    S['weapon'] = idx
    AMMO[idx] = WEAPONS[idx]['mag']
    S['reloading'] = False
    S['reload_id'] += 1
    S['cd'] = .2
    S['hp'] = min(max_hp(), S['hp'] + 20)
    gun.rotation_x = 0
    build_gun()
    flash_msg(f"NEW WEAPON: {WEAPONS[idx]['name']}", 2.0)
    sfx('upgrade')


def on_kill():
    m = S['mode']
    if m == 'ARMS RACE':
        tier = min(len(ARMS_LADDER) - 1, S['kills'] // max(1, int(SET['arms_kills'])))
        if tier != S['tier']:
            S['tier'] = tier
            arms_upgrade()
    if m != 'WAVES':
        lvl = 1 + S['kills'] // KILLS_PER_LEVEL
        if lvl > S['wave']:
            S['wave'] = lvl
            S['hp'] = min(max_hp(), S['hp'] + 15)
            S['shield'] = min(max_shield(), S['shield'] + 15)
            if m == 'SURVIVAL':
                S['points'] += 1
                refresh_skill_menu()
                flash_msg(f'LEVEL {lvl}\n+1 SKILL POINT (TAB)' + maybe_special(), 2.5)
            elif m == 'TIME ATTACK':
                flash_msg(f'LEVEL {lvl}', 1.5)


# ================================================================ القتال
def hurt(amount):
    S['hurt_cd'] = 0.6
    amount = max(1, int(round(amount * SET['dmg_taken'])))
    if S['shield'] > 0:
        absorbed = min(S['shield'], amount)
        S['shield'] -= absorbed
        amount -= absorbed
    S['hp'] -= amount
    shake(.2, 1.2)
    sfx('hurt', 1.0 if amount > 0 else .5)
    if amount > 0:                       # الدم يظهر بس لما الضرر يوصل للصحة
        S['hurt_flash'] = 1.0
        screen_blood(random.randint(2, 4))
    else:
        S['hurt_flash'] = max(S['hurt_flash'], .45)
    if S['hp'] <= 0:
        game_over()


def hit_marker(head):
    sfx('headshot' if head else 'hit', .8)
    hitm.color = C('#e63946') if head else color.white
    hitm.scale = .08 if head else .06
    hitm.enabled = True
    invoke(_off, hitm, delay=.12)


def blast(pos, radius, dmg):
    ball = Entity(model='sphere', position=pos, scale=.5, color=GOLD)
    ball.animate_scale(radius * 2, duration=.2)
    destroy(ball, delay=.22)
    explode(pos, C('#fb8500'), n=18)
    shake(.25, 1.0)
    sfx('boom')
    for e in enemies[:]:
        d = distance(e.world_position + Vec3(0, .9, 0), pos)
        if d < radius:
            e.hit(dmg * (1 - d / radius * .6))
    hit_marker(False)


def fire_ray(direction, w):
    cw = camera.world_position
    fw = camera.forward
    pv = player.pivot.world_position - cw
    origin = cw + fw * max(0.0, pv.x * fw.x + pv.y * fw.y + pv.z * fw.z)   # تخطي أي حاجة بين الكاميرا واللاعب
    ignore = [player, gun]
    end = origin + direction * 150
    for _ in range(w['pierce']):
        info = raycast(origin, direction, distance=150, ignore=ignore)
        if not info.hit:
            break
        end = info.world_point
        e = info.entity
        if isinstance(e, Enemy):
            head = info.world_point.y > e.y + 1.45 * e.scale_y
            dmg = w['dmg'] * dmg_mult() * (head_mult() if head else 1)
            if head and w.get('instakill'):
                dmg = 9999
            e.hit(dmg, head)
            hit_marker(head)
            if head:
                popup('ONE SHOT!' if w.get('instakill') else 'HEADSHOT!', C('#e63946'))
            ignore.append(e)
        else:
            if w['blast']:
                blast(info.world_point, w['blast'], w['dmg'] * dmg_mult())
            else:
                explode(info.world_point, INK, n=3)
            break
    return end


def shoot():
    if S['state'] != 'play' or S['dead'] or S['paused'] or S['pm'] or S['reloading'] or S['cd'] > 0:
        return
    w = cur()
    i = S['weapon']
    if AMMO[i] <= 0:
        sfx('empty')
        reload_gun()
        return
    AMMO[i] -= 1
    S['cd'] = w['rate'] + min(0.0, S['cd'])      # بيحافظ على معدل الإطلاق الحقيقي حتى مع الفريمات
    fast = w['rate'] < .06
    gun.animate_position(GUN_POS + Vec3(0, 0, -.06 if fast else -.2), duration=.03 if fast else .04)
    gun.animate_position(GUN_POS, duration=.06 if fast else .12, delay=.035 if fast else .05)
    sfx(SHOT_SND[w['name']], SHOT_VOL.get(w['name'], 1.0))
    if w['name'] == 'SHOTGUN':
        late_sfx('pump', i, .4, .8)
    elif w['name'] == 'SNIPER':
        late_sfx('bolt', i, .5, .8)
    shake(.05, w['recoil'] * (.4 if S['ads'] else 1))
    muzzle_flash()

    ends = []
    for _ in range(w['pellets']):
        d = camera.forward
        if w['spread']:
            t = math.tan(math.radians(w['spread'] * (.4 if S['ads'] else 1)))
            d = (camera.forward + camera.right * random.uniform(-t, t) +
                 camera.up * random.uniform(-t, t)).normalized()
        ends.append(fire_ray(d, w))
    for end in ends:
        start = flash_ent.world_position if flash_ent is not None else gun.world_position
        tr = Entity(model='cube', color=INK, position=(start + end) / 2,
                    scale=(.025, .025, max(.1, distance(start, end))))
        tr.look_at(end)
        tr.animate_scale((0, 0, tr.scale_z), duration=.09)
        destroy(tr, delay=.1)
    if AMMO[i] == 0 and SET['auto_reload']:
        reload_gun()


def reload_gun():
    i = S['weapon']
    w = cur()
    if S['reloading'] or AMMO[i] == w['mag']:
        return
    S['reloading'] = True
    S['reload_id'] += 1
    rid = S['reload_id']
    t = w['reload'] * reload_mult()
    sfx('mag_out')
    gun.animate_rotation_x(40, duration=.25)
    gun.animate_rotation_x(0, duration=.25, delay=max(.1, t - .3))

    def mag_in():
        if S['reload_id'] == rid and S['reloading']:
            sfx('mag_in')
    invoke(mag_in, delay=max(.15, t - .35))

    def done():
        if S['reload_id'] == rid and S['reloading']:
            AMMO[i] = w['mag']
            S['reloading'] = False
    invoke(done, delay=t)


def next_weapon(step):
    sl = slots()
    if S['weapon'] not in sl:
        return sl[0]
    return sl[(sl.index(S['weapon']) + step) % len(sl)]


def switch_weapon(idx):
    if idx == S['weapon'] or not available(idx) or S['dead'] or S['paused'] or S['pm']:
        return
    S['weapon'] = idx
    S['reloading'] = False
    S['reload_id'] += 1
    S['cd'] = .15
    gun.rotation_x = 0
    build_gun()
    sfx('switch')


def dash():
    if S['dash_cd'] > 0 or S['dead'] or S['paused'] or S['pm']:
        return
    S['dash_cd'] = 2.5
    sfx('dash')
    player.start_dash()
    S['fov_kick'] = 12


# ================================================================ بدء / نهاية اللعب
def game_over(time_up=False):
    S['dead'] = True
    sfx('over')
    S['paused'] = False
    S['pm'] = False
    S['ads'] = False
    S['msg_id'] += 1
    panel.enabled = False
    pause_menu.enabled = False
    scope_ui.enabled = False
    gun.enabled = False
    player.enabled = False
    mouse.locked = False
    camera.fov = SET['fov']
    vig.alpha = .6
    vig.enabled = True
    new_best = save_best(S['score'], S['wave'])
    b = get_best()
    title = 'TIME UP!' if time_up else 'GAME OVER'
    center_msg.text = (f"{title}\n{S['mode']}\nScore: {S['score']}  Kills: {S['kills']}  Level: {S['wave']}\n"
                       f"{'NEW BEST!' if new_best else 'Best: ' + str(b['score'])}\n"
                       f"ENTER = restart    ESC = menu")


def new_run():
    close_overlays()
    for e in enemies[:]:
        destroy(e)
    enemies.clear()
    clear_decals()
    build_map(MAP_NAMES[CFG['map']])
    mode = MODES[CFG['mode']]
    start = START_WAVES[CFG['start']] if mode == 'WAVES' else 1
    S.update(state='play', mode=mode, tier=0, timer=float(SET['time_limit']), spawn_t=.8, pm=False,
             hp=100, shield=50, score=0, wave=(start - 1 if mode == 'WAVES' else 1), dash_cd=0.0,
             dead=False, paused=False, hurt_cd=0.0, kills=0, cd=0.0, reloading=False, has_special=False,
             ads=False, ads_k=0.0, cam_f=1.0, cam_tick=99, cam_ray=1.0, shk_t=0.0, shk_m=0.0, fov_kick=0.0, hurt_flash=0.0,
             lvl={n: 0 for n, _ in SKILLS})
    if mode in ('WAVES', 'SURVIVAL'):
        S['points'] = POINTS_PER_WAVE * start - (POINTS_PER_WAVE if start > 1 else 0)
    else:
        S['points'] = 0
    S['reload_id'] += 1
    S['msg_id'] += 1
    for i, w in enumerate(WEAPONS):
        AMMO[i] = w['mag']
    S['weapon'] = slots()[0]
    gun.rotation_x = 0
    build_gun()
    menu.enabled = False
    panel.enabled = False
    set_play_ui(True)
    camera.fov = SET['fov']
    player.enabled = True
    player.position = (0, 0, 0)
    player.rotation_y = 0
    player.pivot.rotation_x = 0
    player.vy = 0
    mouse.locked = True
    center_msg.text = ''
    refresh_skill_menu()
    if mode == 'WAVES':
        spawn_wave()
    else:
        for _ in range(3):
            spawn_enemy(1)
        intro = {'ARMS RACE': f"ARMS RACE\nEvery {int(SET['arms_kills'])} kills = a stronger weapon",
                 'SURVIVAL': 'SURVIVAL\nHow long can you last?',
                 'TIME ATTACK': f"TIME ATTACK\n{int(SET['time_limit'])} SECONDS - GO!"}[mode]
        flash_msg(intro, 3.0)


btn_play.on_click = new_run


# ================================================================ الحلقة الرئيسية
def update_fx():
    S['t'] += time.dt
    if shine_ent is not None and S['weapon'] == 5:
        shine_ent.z = -.05 + ((S['t'] * .55) % 1.0) * .8
        shine_ent.rotation_z += 220 * time.dt
        shine_ent.scale = .5 + .5 * abs(math.sin(S['t'] * 8))
    S['hurt_flash'] = max(0, S['hurt_flash'] - 1.8 * time.dt)
    low = S['hp'] / max_hp()
    pulse = (.18 + .12 * math.sin(S['t'] * 7)) if low < .3 else 0
    a = max(S['hurt_flash'] * .85, pulse) if SET['vignette'] else 0
    vig.alpha = a
    vig.enabled = a > .01


def update():
    if S['state'] == 'menu':
        player.rotation_y += 6 * time.dt          # الكاميرا بتلف ببطء ورا القائمة
        return
    if S['dead']:
        return
    if S['paused'] or S['pm']:
        refresh_hud()
        return
    S['hurt_cd'] = max(0, S['hurt_cd'] - time.dt)
    S['dash_cd'] = max(0, S['dash_cd'] - time.dt)
    S['cd'] = max(-time.dt, S['cd'] - time.dt)
    S['fov_kick'] = max(0, S['fov_kick'] - 40 * time.dt)
    update_fx()

    # عداد الـ FPS (اختياري من الإعدادات)
    fps_txt.enabled = SET['show_fps']
    if SET['show_fps']:
        S['fps_acc'] += time.dt
        S['fps_n'] += 1
        if S['fps_acc'] >= .5:
            settext(fps_txt, f"FPS {int(S['fps_n'] / S['fps_acc'])}")
            S['fps_acc'] = 0.0
            S['fps_n'] = 0

    # السكوب: تكبير تدريجي
    w = cur()
    target = (w['zoom'] if S['ads'] else SET['fov']) + S['fov_kick']
    camera.fov = lerp(camera.fov, target, min(1, 14 * time.dt))
    update_camera()
    scoped = S['ads'] and w['scope'] and camera.fov < 40 and S['ads_k'] > .8
    scope_ui.enabled = scoped
    gun.enabled = not scoped
    crosshair.enabled = (not scoped) and SET['crosshair']

    if S['hurt_cd'] <= 0 and S['shield'] < max_shield():
        S['shield'] = min(max_shield(), S['shield'] + 2 * time.dt)
    if held_keys['left mouse'] and w['auto']:
        shoot()

    if S['mode'] == 'WAVES':
        if not enemies:
            spawn_wave()
    else:
        continuous_update()
        if S['mode'] == 'TIME ATTACK':
            S['timer'] -= time.dt
            if S['timer'] <= 0:
                S['timer'] = 0
                game_over(True)
                return
    refresh_hud()


def input(key):
    if map_panel.enabled:
        if key == 'escape':
            close_map_picker()
        return
    # --- شاشة الإعدادات
    if settings_panel.enabled:
        if key == 'escape':
            close_settings()
        return
    # --- القائمة الرئيسية
    if S['state'] == 'menu':
        if key == 'escape':
            application.quit()
        elif key == 'enter':
            new_run()
        return
    # --- قائمة الإيقاف
    if S['pm']:
        if key == 'escape':
            close_pause()
        return
    if key == 'escape':
        if S['dead']:
            show_menu()
        elif S['paused']:
            toggle_skills()
        else:
            open_pause()
        return
    if S['dead']:
        if key == 'enter':
            new_run()
        return
    if key == 'tab':
        toggle_skills()
        return
    if S['paused']:
        if len(key) == 1 and key in '123456':
            upgrade(SKILLS[int(key) - 1][0])
        return
    if key == 'left mouse down':
        shoot()
    elif key == 'right mouse down':
        S['ads'] = (not S['ads']) if SET['aim_toggle'] else True
    elif key == 'right mouse up':
        if not SET['aim_toggle']:
            S['ads'] = False
    elif key == 'r':
        reload_gun()
    elif key == 'v':
        S['tp'] = not S['tp']
        S['cam_f'] = 1.0
        S['cam_tick'] = 99
        flash_msg('THIRD PERSON' if S['tp'] else 'FIRST PERSON', 1.2)
    elif key == 'left shift':
        dash()
    elif len(key) == 1 and key in '1234567':
        k = int(key) - 1
        sl = slots()
        if k < len(sl):
            switch_weapon(sl[k])
    elif key == 'scroll up':
        switch_weapon(next_weapon(-1))
    elif key == 'scroll down':
        switch_weapon(next_weapon(1))


build_map(MAP_NAMES[CFG['map']])
set_play_ui(False)
set_body_visible(False)
player.enabled = False
mouse.locked = False
apply_settings()
refresh_main_menu()
app.run()
