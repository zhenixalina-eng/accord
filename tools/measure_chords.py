#!/usr/bin/env python3
"""Меряет по скриншоту, над какой колонкой текста стоит каждый аккорд.

Работает и со светлыми, и с тёмными скринами. Строки аккордов отличает двумя
способами: по цвету (если аккорды выделены цветом) и по плотности — в строке
аккордов закрашено гораздо меньше, чем в строке текста.
"""
import math
import sys
from collections import Counter
from pathlib import Path

from PIL import Image

GAP_ROWS = 2      # столько пустых строк подряд разделяют строки текста


def background(im):
    """Средняя яркость углов — считаем её фоном."""
    w, h = im.size
    px = im.load()
    corners = [px[1, 1], px[w - 2, 1], px[1, h - 2], px[w - 2, h - 2]]
    return sum(sum(c) / 3 for c in corners) / 4


def ink_test(im):
    """Функция «это чернила?» — с учётом того, тёмный фон или светлый."""
    bg = background(im)
    dark_bg = bg < 128
    thr = 60
    if dark_bg:
        return lambda p: (p[0] + p[1] + p[2]) / 3 > bg + thr
    return lambda p: (p[0] + p[1] + p[2]) / 3 < bg - thr


def row_bands(im, is_ink):
    px = im.load()
    w, h = im.size
    rows = []
    for y in range(h):
        rows.append(any(is_ink(px[x, y]) for x in range(0, w, 2)))

    bands, start, empty = [], None, 0
    for y, has in enumerate(rows):
        if has:
            if start is None:
                start = y
            empty = 0
        elif start is not None:
            empty += 1
            if empty >= GAP_ROWS:
                bands.append((start, y - empty + 1))
                start, empty = None, 0
    if start is not None:
        bands.append((start, h))
    return bands


def ink_columns(im, band, is_ink):
    px = im.load()
    y0, y1 = band
    return [any(is_ink(px[x, y]) for y in range(y0, y1)) for x in range(im.size[0])]


def clusters_from(cols, min_gap):
    out, start, gap = [], None, 0
    for x, has in enumerate(cols):
        if has:
            if start is None:
                start = x
            gap = 0
        elif start is not None:
            gap += 1
            if gap >= min_gap:
                out.append((start, x - gap))
                start, gap = None, 0
    if start is not None:
        out.append((start, len(cols) - 1))
    return out


def band_tint(im, band, is_ink):
    """Средний цвет чернил полосы."""
    px = im.load()
    y0, y1 = band
    rs = gs = bs = n = 0
    for y in range(y0, y1):
        for x in range(im.size[0]):
            p = px[x, y]
            if is_ink(p):
                rs, gs, bs, n = rs + p[0], gs + p[1], bs + p[2], n + 1
    return (rs / n, gs / n, bs / n) if n else (0, 0, 0)


def all_glyph_lefts(im, bands, is_ink):
    xs = []
    for band in bands:
        xs += [a for a, _ in clusters_from(ink_columns(im, band, is_ink), min_gap=2)]
    return xs


def estimate_cell(im, bands, is_ink):
    """Ширина знакоместа — дробная, иначе на длинных строках копится сдвиг.

    Сначала берём самый частый шаг между соседними глифами, потом уточняем:
    у верной ширины все глифы попадают близко к целым номерам колонок.
    """
    deltas = Counter()
    for band in bands:
        cl = clusters_from(ink_columns(im, band, is_ink), min_gap=2)
        for a, b in zip(cl, cl[1:]):
            d = b[0] - a[0]
            if 5 < d < 60:
                deltas[d] += 1
    if not deltas:
        sys.exit('не удалось оценить ширину знакоместа')
    rough = deltas.most_common(1)[0][0]

    xs = all_glyph_lefts(im, bands, is_ink)
    best, best_score = rough, -1
    step = 0.01
    c = rough - 1.5
    while c <= rough + 1.5:
        if c > 1:
            # насколько дружно доли колонок жмутся к нулю
            re = im_ = 0.0
            for x in xs:
                ph = ((x - xs[0]) / c % 1) * 2 * math.pi
                re += math.cos(ph)
                im_ += math.sin(ph)
            score = (re * re + im_ * im_) ** 0.5 / len(xs)
            if score > best_score:
                best, best_score = c, score
        c += step
    return best


def split_two(values):
    """Простое разделение на две группы по одному числу (2-means)."""
    lo, hi = min(values), max(values)
    for _ in range(20):
        groups = [[], []]
        for v in values:
            groups[abs(v - hi) < abs(v - lo)].append(v)
        if not groups[0] or not groups[1]:
            break
        lo2, hi2 = sum(groups[0]) / len(groups[0]), sum(groups[1]) / len(groups[1])
        if (lo2, hi2) == (lo, hi):
            break
        lo, hi = lo2, hi2
    return lo, hi


def classify(im, bands, is_ink):
    """Для каждой полосы: строка аккордов или текста."""
    tints = [band_tint(im, b, is_ink) for b in bands]
    # Цветные аккорды: у них заметно другой оттенок, чем у текста.
    tinted = [abs(t[1] - t[0]) + abs(t[2] - t[0]) for t in tints]
    if max(tinted) - min(tinted) > 40:
        cut = (max(tinted) + min(tinted)) / 2
        return [t > cut for t in tinted]

    # Иначе по плотности: в строке аккордов закрашено куда меньше.
    density = [sum(ink_columns(im, b, is_ink)) / im.size[0] for b in bands]
    lo, hi = split_two(density)
    cut = (lo + hi) / 2
    return [d < cut for d in density]


def main(path):
    im = Image.open(path).convert('RGB')
    is_ink = ink_test(im)
    bands = row_bands(im, is_ink)
    if not bands:
        sys.exit('текстовых строк не найдено')

    cell = estimate_cell(im, bands, is_ink)
    is_chord = classify(im, bands, is_ink)

    lefts = []
    for band, chord in zip(bands, is_chord):
        if chord:
            continue
        cl = clusters_from(ink_columns(im, band, is_ink), min_gap=max(3, int(cell // 2)))
        if cl:
            lefts.append(cl[0][0])
    if not lefts:
        sys.exit('строк текста не найдено')
    x0 = min(lefts)

    fon = 'тёмный' if background(im) < 128 else 'светлый'
    print(f'{Path(path).name}: {im.size[0]}x{im.size[1]}, фон {fon}, знакоместо={cell:.2f}px, левый край={x0}px')
    print()
    for band, chord in zip(bands, is_chord):
        cl = clusters_from(ink_columns(im, band, is_ink), min_gap=max(3, int(cell // 2)))
        cols = [round((a - x0) / cell) for a, _ in cl]
        kind = 'аккорды' if chord else '  текст'
        print(f'{kind} y={band[0]:4d}: {cols}')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else sys.exit('укажи путь к картинке'))
