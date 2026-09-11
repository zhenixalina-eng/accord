#!/usr/bin/env python3
"""Ставит [Аккорд] в текст песни на заданные колонки моноширинной сетки.

Колонка = индекс символа в строке текста, над которым должен стоять аккорд
(именно так их меряет measure_chords.py по скриншоту).
"""


def place(lyric, chords):
    """chords: [(колонка, 'Am'), ...] -> строка вида '[Am]текст'."""
    chords = sorted(chords)
    need = max((col for col, _ in chords), default=0)
    if len(lyric) < need:
        lyric = lyric.ljust(need)
    out, prev = [], 0
    for col, name in chords:
        out.append(lyric[prev:col])
        out.append(f'[{name}]')
        prev = col
    out.append(lyric[prev:])
    return ''.join(out)


def strip_chords(line):
    out, i = [], 0
    while i < len(line):
        if line[i] == '[':
            i = line.index(']', i) + 1
        else:
            out.append(line[i])
            i += 1
    return ''.join(out)
