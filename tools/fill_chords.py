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
    """Номер слога (с 1), на который попадает аккорд в колонке col.

    Берём ближайшую гласную в обе стороны: аккорд, подписанный над серединой
    слова, относится к его слогу, а не к началу следующего слова.
    """
    vp = vowel_positions(line)
    if not vp:
        return 1
    best = min(range(len(vp)), key=lambda i: (abs(vp[i] - col), i))
    return best + 1


def vowel_to_column(line, n):
    """Колонка гласной номер n (с 1); если слогов меньше — последняя."""
    vp = vowel_positions(line)
    if not vp:
        return 0
    return vp[min(n, len(vp)) - 1]


def space_out(chords):
    """Раздвигает аккорды, попавшие на смежные колонки, чтобы не слиплись в «EmC»."""
    out = []
    for col, name in sorted(chords):
        if out:
            prev_col, prev_name = out[-1]
            col = max(col, prev_col + len(prev_name) + 1)
        out.append((col, name))
    return out


def transfer(ref_line, ref_chords, target_line):
    """ref_chords: [(колонка, 'Am'), ...] с размеченной строки -> то же для target_line.

    Строки разной длины, поэтому после переноса аккорды могут оказаться вплотную —
    раздвигаем их, иначе в строке аккордов будет нечитаемое «EmC».
    """
    out = []
    for col, name in ref_chords:
        n = column_to_vowel(ref_line, col)
        out.append((vowel_to_column(target_line, n), name))
    return space_out(out)
