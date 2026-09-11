#!/usr/bin/env python3
"""Печатает песню так, как она будет выглядеть на сайте: строка аккордов над строкой текста."""
import io
import sys
from pathlib import Path


def render(path):
    src = io.open(path, encoding='utf-8').read().rstrip('\n').split('\n')
    body = src[src.index('') + 1:] if '' in src else src
    lines = []
    for raw in body:
        if not raw.strip():
            lines.append(('', ''))
            continue
        lyric, chords, i = '', [], 0
        while i < len(raw):
            if raw[i] == '[':
                end = raw.index(']', i)
                chords.append((len(lyric), raw[i + 1:end]))
                i = end + 1
            else:
                lyric += raw[i]
                i += 1
        row, filled = '', 0
        for pos, name in chords:
            row += ' ' * (pos - filled) + name
            filled = pos + len(name)
        lines.append((row, lyric))
    return lines


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit('укажи путь к файлу песни')
    for row, lyric in render(Path(sys.argv[1])):
        if not lyric:
            print()
        else:
            print(row)
            print(lyric)
