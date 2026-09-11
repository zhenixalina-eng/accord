#!/usr/bin/env python3
"""Переносит аккорды с размеченной строки на неразмеченную по позиции слога.

Колонку нельзя копировать как есть: строки разной длины, и аккорд уедет не туда.
Зато строки одного куплета поются на одну мелодию, поэтому смена аккорда
приходится на тот же по счёту слог. Слоги считаем по гласным.
"""
VOWELS = 'аеёиоуыэюяАЕЁИОУЫЭЮЯ'


def vowel_positions(line):
    return [i for i, ch in enumerate(line) if ch in VOWELS]


def column_to_vowel(line, col):
    """Номер слога (с 1), на который попадает аккорд в колонке col."""
    vp = vowel_positions(line)
    if not vp:
        return 1
    # ближайшая гласная, начиная с этой колонки; если аккорд левее первой — слог 1
    for n, pos in enumerate(vp, start=1):
        if pos >= col:
            return n
    return len(vp)


def vowel_to_column(line, n):
    """Колонка гласной номер n (с 1); если слогов меньше — последняя."""
    vp = vowel_positions(line)
    if not vp:
        return 0
    return vp[min(n, len(vp)) - 1]


def transfer(ref_line, ref_chords, target_line):
    """ref_chords: [(колонка, 'Am'), ...] с размеченной строки -> то же для target_line."""
    out = []
    for col, name in ref_chords:
        n = column_to_vowel(ref_line, col)
        out.append((vowel_to_column(target_line, n), name))
    return out
