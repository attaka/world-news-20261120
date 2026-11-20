#!/usr/bin/env python3
"""Sum up 20 November 2026's world news in one image.

A self-contained Python program (standard library only, no network)
that draws a newspaper front page of the day as a PNG and writes it
to /output/entry.png. The drawing is fully deterministic: the same
program always produces the same bytes.

Run:  python3 main.py
"""

import os
import struct
import zlib

# ---------------------------------------------------------------- font
# A 5x7 pixel font, one glyph per character, rows top to bottom.
# '#' is ink, '.' is empty. Text is rendered upper-case only.

FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", ".#.#.", "..#..", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#...#", "##..#", "#.#.#", "#..##", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    "'": (".##..", ".##..", ".#...", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "(": ("...##", "..#..", ".#...", ".#...", ".#...", "..#..", "...##"),
    ")": (".##..", "..#..", "...#.", "...#.", "...#.", "..#..", ".##.."),
    "&": (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    "%": ("##..#", "##.#.", "....#", "...#.", "..#..", ".#...", "#..##"),
    "+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "$": ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    "=": (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    "*": (".....", ".#.#.", "..#..", "#####", "..#..", ".#.#.", "....."),
    "<": ("....#", "...#.", "..#..", ".#...", "..#..", "...#.", "....#"),
    ">": ("#....", ".#...", "..#..", "...#.", "..#..", ".#...", "#...."),
    '"': (".#.#.", ".#.#.", ".....", ".....", ".....", ".....", "....."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
}

# ------------------------------------------------------------- colours

PAPER = (247, 244, 233)
CARD = (255, 254, 248)
INK = (24, 26, 32)
GRAY = (96, 94, 88)
RED = (178, 34, 40)
NAVY = (23, 48, 92)
TEAL = (0, 105, 110)
GOLD = (186, 128, 0)
GREEN = (34, 110, 60)
PURPLE = (96, 54, 140)
BROWN = (140, 84, 30)
SKY = (52, 110, 170)

W = 1024
H = 1024

# -------------------------------------------------------------- canvas


class Canvas:
    """A tiny RGB raster with just the primitives the page needs."""

    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i] = color[0]
            self.px[i + 1] = color[1]
            self.px[i + 2] = color[2]

    def rect(self, x, y, w, h, color):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, color)

    def frame(self, x, y, w, h, color, t=2):
        self.rect(x, y, w, t, color)
        self.rect(x, y + h - t, w, t, color)
        self.rect(x, y, t, h, color)
        self.rect(x + w - t, y, t, h, color)

    def line(self, x0, y0, x1, y1, color, t=2):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        r = t // 2
        while True:
            self.rect(x0 - r, y0 - r, t, t, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, color, fill=True, t=2):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d2 = (xx - cx) * (xx - cx) + (yy - cy) * (yy - cy)
                if fill and d2 <= r * r:
                    self.set(xx, yy, color)
                if not fill and abs(d2 - r * r) <= r * t:
                    self.set(xx, yy, color)

    def poly(self, pts, color):
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        for yy in range(min(ys), max(ys) + 1):
            for xx in range(min(xs), max(xs) + 1):
                inside = False
                j = len(pts) - 1
                for i in range(len(pts)):
                    xi, yi = pts[i]
                    xj, yj = pts[j]
                    if (yi > yy) != (yj > yy):
                        xint = (xj - xi) * (yy - yi) / (yj - yi) + xi
                        if xx < xint:
                            inside = not inside
                    j = i
                if inside:
                    self.set(xx, yy, color)


# ---------------------------------------------------------------- text

ADV = 6  # character advance in glyph units (5 wide + 1 space)


def text_w(s, scale):
    return len(s) * ADV * scale


def draw_text(cv, x, y, s, scale, color, bold=False):
    s = s.upper()
    cx = x
    for ch in s:
        glyph = FONT.get(ch, FONT[" "])
        for row_i, row in enumerate(glyph):
            for col_i, cell in enumerate(row):
                if cell == "#":
                    cv.rect(cx + col_i * scale, y + row_i * scale,
                            scale, scale, color)
                    if bold:
                        cv.rect(cx + col_i * scale + scale, y + row_i * scale,
                                scale, scale, color)
        cx += ADV * scale + (scale if bold else 0)
    return cx - x


def text_w_bold(s, scale, bold=False):
    adv = ADV * scale + (scale if bold else 0)
    return len(s) * adv


def center_text(cv, y, s, scale, color, bold=False):
    w = text_w_bold(s, scale, bold)
    draw_text(cv, (W - w) // 2, y, s, scale, color, bold)
    return 7 * scale


def wrap(s, scale, max_w, bold=False):
    words = s.upper().split()
    lines = []
    cur = ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_w_bold(trial, scale, bold) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_block(cv, x, y, s, scale, color, max_w, bold=False, leading=3):
    lines = wrap(s, scale, max_w, bold)
    for i, ln in enumerate(lines):
        draw_text(cv, x, y + i * (7 * scale + leading), ln, scale, color, bold)
    return len(lines) * (7 * scale + leading)


# --------------------------------------------------------------- icons
# Each icon is drawn inside a box of side s at (x, y) in one colour.


def icon(cv, kind, x, y, s, color):
    cx = x + s // 2
    cy = y + s // 2
    if kind == "globe":
        import math
        cv.circle(cx, cy, s // 2 - 2, color, fill=False, t=3)
        cv.line(cx - s // 2 + 2, cy, cx + s // 2 - 2, cy, color, 2)
        cv.line(cx, cy - s // 2 + 2, cx, cy + s // 2 - 2, color, 2)
        r = s // 2 - 2
        for k in (0.5,):
            prev = None
            for deg in range(0, 361, 6):
                a = math.radians(deg)
                pt = (cx + int(r * k * math.cos(a)),
                      cy + int(r * math.sin(a)))
                if prev:
                    cv.line(prev[0], prev[1], pt[0], pt[1], color, 2)
                prev = pt
    elif kind == "flags":
        cv.line(x + 13, y + s - 4, x + 13, y + 5, color, 3)
        cv.rect(x + 13, y + 5, 23, 13, color)
        cv.rect(x + 4, y + s - 4, s - 8, 3, color)
    elif kind == "chart_up":
        cv.line(x + 4, y + s - 4, x + s - 4, y + s - 4, color, 3)
        cv.line(x + 4, y + s - 4, x + 4, y + 4, color, 3)
        pts = [(x + 8, y + s - 14), (x + s // 3, y + s // 2),
               (x + s // 2, y + s - 22), (x + s - 10, y + 10)]
        for a, b in zip(pts, pts[1:]):
            cv.line(a[0], a[1], b[0], b[1], color, 4)
        cv.poly([(x + s - 10, y + 10), (x + s - 22, y + 12),
                 (x + s - 12, y + 22)], color)
    elif kind == "chart_down":
        cv.line(x + 4, y + s - 4, x + s - 4, y + s - 4, color, 3)
        cv.line(x + 4, y + s - 4, x + 4, y + 4, color, 3)
        pts = [(x + 8, y + 12), (x + s // 3, y + s // 2),
               (x + s // 2, y + 20), (x + s - 10, y + s - 12)]
        for a, b in zip(pts, pts[1:]):
            cv.line(a[0], a[1], b[0], b[1], color, 4)
        cv.poly([(x + s - 10, y + s - 12), (x + s - 22, y + s - 14),
                 (x + s - 12, y + s - 24)], color)
    elif kind == "rocket":
        cv.poly([(cx, y + 2), (cx + 10, y + s // 2), (cx + 6, y + s - 14),
                 (cx - 6, y + s - 14), (cx - 10, y + s // 2)], color)
        cv.poly([(cx - 10, y + s // 2), (cx - 18, y + s - 6),
                 (cx - 6, y + s - 14)], color)
        cv.poly([(cx + 10, y + s // 2), (cx + 18, y + s - 6),
                 (cx + 6, y + s - 14)], color)
        cv.poly([(cx - 4, y + s - 12), (cx + 4, y + s - 12),
                 (cx, y + s - 1)], GOLD)
        cv.circle(cx, y + s // 3, 4, PAPER)
    elif kind == "chip":
        cv.frame(cx - 14, cy - 14, 28, 28, color, 4)
        cv.frame(cx - 6, cy - 6, 12, 12, color, 3)
        for i in range(-1, 2):
            cv.line(cx + i * 10, cy - 22, cx + i * 10, cy - 14, color, 3)
            cv.line(cx + i * 10, cy + 14, cx + i * 10, cy + 22, color, 3)
            cv.line(cx - 22, cy + i * 10, cx - 14, cy + i * 10, color, 3)
            cv.line(cx + 14, cy + i * 10, cx + 22, cy + i * 10, color, 3)
    elif kind == "cloud":
        cv.circle(cx - 10, cy + 2, 11, color)
        cv.circle(cx + 8, cy + 2, 13, color)
        cv.circle(cx, cy - 6, 12, color)
        cv.rect(cx - 20, cy, 42, 12, color)
        for dx in (-14, 0, 14):
            cv.line(cx + dx, cy + 18, cx + dx - 4, cy + 26, SKY, 3)
    elif kind == "sun":
        cv.circle(cx, cy, 11, GOLD)
        import math
        for deg in range(0, 360, 45):
            a = math.radians(deg)
            cv.line(cx + int(16 * math.cos(a)), cy + int(16 * math.sin(a)),
                    cx + int(23 * math.cos(a)), cy + int(23 * math.sin(a)),
                    GOLD, 3)
    elif kind == "cross":
        cv.rect(cx - 6, cy - 20, 12, 40, RED)
        cv.rect(cx - 18, cy - 8, 36, 12, RED)
    elif kind == "ball":
        cv.circle(cx, cy, s // 2 - 3, color, fill=False, t=3)
        cv.poly([(cx, cy - 8), (cx + 8, cy - 2), (cx + 5, cy + 7),
                 (cx - 5, cy + 7), (cx - 8, cy - 2)], color)
        cv.line(cx, cy - 8, cx, cy - s // 2 + 3, color, 2)
        cv.line(cx + 8, cy - 2, cx + s // 2 - 4, cy - 6, color, 2)
        cv.line(cx - 8, cy - 2, cx - s // 2 + 4, cy - 6, color, 2)
    elif kind == "trophy":
        cv.poly([(cx - 14, y + 6), (cx + 14, y + 6), (cx + 10, y + 24),
                 (cx - 10, y + 24)], GOLD)
        cv.line(cx - 14, y + 10, cx - 22, y + 6, GOLD, 4)
        cv.line(cx + 14, y + 10, cx + 22, y + 6, GOLD, 4)
        cv.rect(cx - 3, y + 24, 6, 8, GOLD)
        cv.rect(cx - 10, y + 32, 20, 5, GOLD)
    elif kind == "crown":
        cv.poly([(x + 4, y + s - 10), (x + 4, y + 14), (x + 14, y + 24),
                 (cx, y + 10), (x + s - 14, y + 24), (x + s - 4, y + 14),
                 (x + s - 4, y + s - 10)], GOLD)
    elif kind == "scales":
        cv.line(cx, y + 6, cx, y + s - 12, color, 3)
        cv.line(x + 8, y + 12, x + s - 8, y + 12, color, 3)
        for px_ in (x + 8, x + s - 8):
            cv.line(px_, y + 12, px_ - 7, y + 26, color, 2)
            cv.line(px_, y + 12, px_ + 7, y + 26, color, 2)
            cv.poly([(px_ - 9, y + 26), (px_ + 9, y + 26),
                     (px_, y + 33)], color)
        cv.rect(cx - 12, y + s - 10, 24, 4, color)
    elif kind == "flame":
        cv.poly([(cx, y + 2), (cx + 12, y + 22), (cx + 13, y + s - 8),
                 (cx + 5, y + s - 2), (cx - 5, y + s - 2),
                 (cx - 13, y + s - 8), (cx - 12, y + 22)], RED)
        cv.poly([(cx, y + 18), (cx + 6, y + 30), (cx + 4, y + s - 8),
                 (cx - 4, y + s - 8), (cx - 6, y + 30)], GOLD)
    elif kind == "wave":
        import math
        for row, off in ((0, 0), (12, 8), (24, 0)):
            for xx in range(x + 2, x + s - 2):
                yy = cy + row - 10 + int(5 * math.sin((xx + off) / 6.0))
                cv.rect(xx, yy, 2, 3, SKY)
    elif kind == "plane":
        cv.poly([(x + 2, cy), (x + s - 12, cy - 4), (x + s - 2, cy),
                 (x + s - 12, cy + 4)], color)
        cv.poly([(cx, cy - 2), (cx - 8, cy - 16), (cx + 2, cy - 16),
                 (cx + 8, cy - 2)], color)
        cv.poly([(x + 4, cy), (x - 2 + 8, cy - 12), (x + 14, cy - 12),
                 (x + 12, cy)], color)
    elif kind == "bolt":
        cv.poly([(cx + 6, y + 2), (cx - 10, y + s // 2), (cx - 1, y + s // 2),
                 (cx - 6, y + s - 2), (cx + 12, y + s // 2 - 6),
                 (cx + 2, y + s // 2 - 6)], GOLD)
    elif kind == "film":
        cv.frame(x + 6, y + 8, s - 12, s - 16, color, 3)
        for yy in range(y + 12, y + s - 12, 8):
            cv.rect(x + 9, yy, 3, 4, color)
            cv.rect(x + s - 12, yy, 3, 4, color)
        cv.poly([(cx - 5, cy - 8), (cx - 5, cy + 8), (cx + 9, cy)], RED)
    elif kind == "ballot":
        cv.frame(x + 8, y + 16, s - 16, s - 24, color, 3)
        cv.rect(x + 16, y + 4, s - 32, 16, CARD)
        cv.frame(x + 16, y + 4, s - 32, 16, color, 3)
        cv.line(x + 20, y + 12, x + 25, y + 17, GREEN, 3)
        cv.line(x + 25, y + 17, x + s - 20, y + 7, GREEN, 3)
        cv.rect(x + 14, y + 26, s - 28, 3, color)
    elif kind == "leaf":
        cv.poly([(cx, y + 4), (cx + 16, y + 14), (cx + 14, y + s - 12),
                 (cx, y + s - 4), (cx - 14, y + s - 12),
                 (cx - 16, y + 14)], GREEN)
        cv.line(cx, y + s - 4, cx, y + 12, PAPER, 2)
    elif kind == "court":
        cv.poly([(x + 4, y + 16), (cx, y + 4), (x + s - 4, y + 16)], color)
        cv.rect(x + 4, y + 18, s - 8, 4, color)
        for i in range(4):
            xx = x + 9 + i * (s - 18) // 3
            cv.rect(xx - 2, y + 26, 4, s - 40, color)
        cv.rect(x + 4, y + s - 12, s - 8, 4, color)
    else:  # fallback: a plain diamond
        cv.poly([(cx, y + 4), (x + s - 4, cy), (cx, y + s - 4),
                 (x + 4, cy)], color)


# -------------------------------------------------------------- stories
# The verified news of Friday 20 November 2026, cross-checked across
# Reuters, AP, BBC, Al Jazeera, NHK and other wires on the day.
# Wording stays faithful: claims are framed as claims, and follow-ups
# to Thursday events are framed as Friday developments.

LEAD = {
    "tag": "TOP STORY",
    "region": "EUROPE",
    "head": "RUSSIAN MISSILES LAND IN POLAND",
    "body": "MOSCOW FIRED 400+ DRONES AND 110 MISSILES AT UKRAINE "
            "OVERNIGHT; TWO MISSILES AND A DRONE CAME DOWN IN POLAND.",
    "icon": "flame",
    "color": RED,
}

CARDS = [
    {"tag": "AMERICAS", "head": "TRUMP: PUTIN TALKS GOOD, NO DEAL",
     "body": "HE CALLED THE TALKS VERY GOOD; NO UKRAINE DEAL "
             "WAS ANNOUNCED.",
     "icon": "flags", "color": NAVY},
    {"tag": "EUROPE", "head": "UK AND EU AGREE RESET DEAL",
     "body": "FOOD CHECKS EASED, CARBON MARKETS LINKED, YOUTH "
             "SCHEME LAUNCHED.",
     "icon": "chart_up", "color": TEAL},
    {"tag": "MIDDLE EAST", "head": "SAUDI INTERCEPTS HOUTHI MISSILES",
     "body": "FRIDAY INTERCEPTIONS AFTER THURSDAY HIT ON "
             "RIYADH TOWER.",
     "icon": "flame", "color": BROWN},
    {"tag": "BUSINESS", "head": "ANTHROPIC SLIDES AFTER RECORD IPO",
     "body": "SHARES FELL 9% IN A GLOBAL TECH SELL-OFF AFTER "
             "THE DEBUT.",
     "icon": "chart_down", "color": RED},
    {"tag": "ASIA", "head": "INDONESIA, CHINA DISCUSS SEA TIES",
     "body": "PRABOWO MET XI ON TRADE, INVESTMENT AND SEA "
             "COOPERATION.",
     "icon": "wave", "color": SKY},
    {"tag": "SCIENCE", "head": "PROBE AT MERCURY AFTER 8 YEARS",
     "body": "EUROPE-JAPAN BEPICOLOMBO ARRIVED; ORBIT BURN "
             "DUE SATURDAY.",
     "icon": "rocket", "color": PURPLE},
]

MINIS = [
    {"tag": "TECH", "head": "SIGNAL BLOCKS SCREENSHOTS",
     "body": "TO STOP AGENT ACCESS", "icon": "chip", "color": SKY},
    {"tag": "HEALTH", "head": "CANCER PILL: EARLY PROMISE",
     "body": "TUMOURS GONE IN 1 IN 12", "icon": "cross", "color": RED},
    {"tag": "CULTURE", "head": "GTA VI DAY-ONE SALES RECORD",
     "body": "SALES HIT $3.79 BILLION", "icon": "film", "color": PURPLE},
    {"tag": "EUROPE", "head": "COST-OF-LIVING PROTESTS EUROPE",
     "body": "RALLIES IN 7 COUNTRIES", "icon": "ballot", "color": GOLD},
    {"tag": "AFRICA", "head": "581 WOMEN KILLED IN SOUTH AFRICA",
     "body": "FIGURES FOR JULY-SEPT", "icon": "sun", "color": GREEN},
    {"tag": "SPORT", "head": "ALCARAZ PERFECT AT ATP FINALS",
     "body": "BEAT COBOLLI 6-4 6-1", "icon": "ball", "color": TEAL},
]

TICKER = [
    "ROHINGYA WELCOME ICJ VERDICT",
    "CHINA TELLS JAPAN TO CHANGE TONE",
    "IRAQ DEPLOYS NEAR MILITIA BASE",
    "MARATHON CHAMPION BANNED 3 YEARS",
]


# --------------------------------------------------------------- layout

MARGIN = 30
INNER = W - 2 * MARGIN


def section_bar(cv, y, label, color):
    cv.rect(MARGIN, y, INNER, 30, color)
    draw_text(cv, MARGIN + 14, y + 5, label, 3, CARD, bold=True)
    return y + 30 + 4


def lead_panel(cv, y, story):
    h = 160
    cv.rect(MARGIN, y, INNER, h, CARD)
    cv.rect(MARGIN, y, 12, h, story["color"])
    tx = MARGIN + 34
    draw_text(cv, tx, y + 16, story["tag"] + " - " + story["region"],
              2, story["color"], bold=True)
    used = draw_block(cv, tx, y + 44, story["head"], 5, INK,
                      INNER - 220, bold=True, leading=3)
    draw_block(cv, tx, y + 44 + used + 6, story["body"], 2, GRAY,
               INNER - 220, leading=2)
    icon(cv, story["icon"], W - MARGIN - 150, y + 34, 108, story["color"])
    return y + h + 8


def card(cv, x, y, w, h, story):
    cv.rect(x, y, w, h, CARD)
    cv.rect(x, y, w, 6, story["color"])
    draw_text(cv, x + 14, y + 12, story["tag"], 2, story["color"], bold=True)
    icon(cv, story["icon"], x + w - 58, y + 10, 44, story["color"])
    used = draw_block(cv, x + 14, y + 34, story["head"], 3, INK,
                      w - 84, bold=True, leading=2)
    draw_block(cv, x + 14, y + 34 + used + 3, story["body"], 2, GRAY,
               w - 28, leading=1)


def mini(cv, x, y, w, h, story):
    cv.rect(x, y, w, h, CARD)
    cv.rect(x, y, 6, h, story["color"])
    draw_text(cv, x + 16, y + 10, story["tag"], 2, story["color"], bold=True)
    used = draw_block(cv, x + 16, y + 30, story["head"], 2, INK,
                      w - 26, bold=True, leading=2)
    draw_block(cv, x + 16, y + 30 + used + 2, story["body"], 2, GRAY,
               w - 26, leading=3)


def build():
    cv = Canvas(W, H, PAPER)
    cv.frame(10, 10, W - 20, H - 20, INK, 3)
    cv.frame(18, 18, W - 36, H - 36, INK, 1)

    y = 26
    center_text(cv, y, "THE WORLD IN ONE DAY", 3, INK, bold=True)
    y += 26
    cv.rect(MARGIN, y, INNER, 4, RED)
    y += 10
    center_text(cv, y, "20 NOVEMBER 2026", 7, INK, bold=True)
    y += 54
    center_text(cv, y,
                "FRIDAY - EVERY STORY HAPPENED OR WAS FIRST REPORTED ON THIS DAY",
                2, RED, bold=True)
    y += 20
    cv.rect(MARGIN, y, INNER, 4, INK)
    y += 12

    y = lead_panel(cv, y, LEAD)
    y = section_bar(cv, y, "AROUND THE WORLD", NAVY)

    gap = 10
    cw = (INNER - gap) // 2
    ch = 118
    for i, story in enumerate(CARDS):
        cx = MARGIN + (i % 2) * (cw + gap)
        cy = y + (i // 2) * (ch + gap)
        card(cv, cx, cy, cw, ch, story)
    y += 3 * (ch + gap) - 2

    y = section_bar(cv, y, "MORE OF THE DAY", TEAL)
    mw = (INNER - 2 * gap) // 3
    mh = 80
    for i, story in enumerate(MINIS):
        cx = MARGIN + (i % 3) * (mw + gap)
        cy = y + (i // 3) * (mh + gap)
        mini(cv, cx, cy, mw, mh, story)
    y += 2 * (mh + gap)

    ticker = "ALSO TODAY:  " + "  *  ".join(TICKER)
    used = draw_block(cv, MARGIN, y, ticker, 2, INK, INNER, leading=3)
    y += used + 4
    center_text(cv, y,
                "SOURCES: REUTERS - AP - BBC - AL JAZEERA - NHK - DRAWN IN CODE BY AN AI AGENT",
                2, GRAY)
    return cv


# ----------------------------------------------------------------- png


def png_bytes(cv):
    raw = bytearray()
    row = cv.w * 3
    for yy in range(cv.h):
        raw.append(0)
        raw += cv.px[yy * row:(yy + 1) * row]

    def chunk(tag, data):
        body = tag + data
        return (struct.pack(">I", len(data)) + body +
                struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) +
            chunk(b"IDAT", zlib.compress(bytes(raw), 9)) +
            chunk(b"IEND", b""))


def main():
    data = png_bytes(build())
    out = "/output/entry.png"
    try:
        os.makedirs("/output", exist_ok=True)
    except OSError:
        out = os.path.join("output", "entry.png")
        os.makedirs("output", exist_ok=True)
    with open(out, "wb") as f:
        f.write(data)
    print("wrote", out, len(data), "bytes")


if __name__ == "__main__":
    main()
