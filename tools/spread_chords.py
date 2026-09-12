#!/usr/bin/env python3
"""Ищет строки без аккордов и достраивает их по соседним строкам с аккордами.

В подборах часто аккорды выписаны только над первыми строками куплета, а дальше
подразумевается «тот же круг». Играть по такому листу неудобно, поэтому круг
раскладывается на каждую строку.

Как раскладывается: берём опорную строку с аккордами и переносим не колонки
(строки разной длины — уедет), а доли: аккорд, стоявший на трети опорной строки,
встаёт на треть новой. Потом позиция садится на ближайшее начало слова, чтобы
аккорд не оказался в середине слога. Замыкающий аккорд опорной строки остаётся
замыкающим — висит в конце строки.

Если перед пропуском две разные строки с аккордами (обычная вилка «первая строка
куплета — вторая строка куплета»), они чередуются.

Запуск:  python3 tools/spread_chords.py            — показать, что будет достроено
         python3 tools/spread_chords.py --apply    — записать
         python3 tools/spread_chords.py songs/x.txt — только одна песня
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from place_chords import place, strip_chords

SONGS = Path(__file__).resolve().parent.parent / 'songs'

# строки, которые не текст песни: подписи разделов, пометки в скобках, табулатура
LABEL = re.compile(r'^(припев|проигрыш|вступление|кода|куплет|бридж|интро|аутро)\b.*:?\s*$', re.I)
NOTE = re.compile(r'^\s*\(.*\)\s*$')
TAB = re.compile(r'^[\s\-0-9|/\\hpbxv~*()]+$')
META = re.compile(r'^(key|title|artist|lyrics|capo):', re.I)   # строка «key: Am» у варианта
SHORT = 12          # строку короче этого не нагружаем целым кругом
MIN_GAP = 5         # ближе этого аккорды ставить не стоит — читается как каша


def parse(raw):
    """Строка файла -> (текст без аккордов, [(колонка, аккорд), ...])."""
    lyric, chords, i = '', [], 0
    while i < len(raw):
        if raw[i] == '[':
            end = raw.index(']', i)
            chords.append((len(lyric), raw[i + 1:end]))
            i = end + 1
        else:
            lyric += raw[i]
            i += 1
    return lyric, chords


def is_lyric(lyric):
    """Это строка текста, которую можно нагрузить аккордами?"""
    s = lyric.strip()
    return bool(s) and not LABEL.match(s) and not NOTE.match(s) and not TAB.match(s) \
        and not META.match(s)


def word_starts(text):
    starts, prev = [], ' '
    for i, c in enumerate(text):
        if c != ' ' and prev == ' ':
            starts.append(i)
        prev = c
    return starts


def pick(chords, k):
    """k аккордов из круга — равномерно, но первый и последний обязательно.

    Короткая строка поётся быстрее, и весь круг на неё не ложится: аккорды
    встают вплотную и читаются как каша. Поэтому берём из круга столько,
    сколько строка вмещает по своей длине.
    """
    if k >= len(chords):
        return chords
    if k <= 1:
        return chords[:1]
    idx = sorted({round(i * (len(chords) - 1) / (k - 1)) for i in range(k)})
    return [chords[i] for i in idx]


def spread(ref_lyric, ref_chords, text):
    """Круг опорной строки, разнесённый по длине новой строки."""
    n = len(ref_lyric.rstrip()) or 1
    body = len(text.rstrip())
    chords = pick(ref_chords, max(1, round(body / n * len(ref_chords))))
    starts = word_starts(text)
    out, floor = [], -1
    for col, name in chords:
        want = col / n * body
        if want >= body - 1:                      # замыкающий — в конец строки
            place_at = max(body, floor + 1)
        else:
            free = [s for s in starts if s >= floor]
            place_at = min(free, key=lambda s: abs(s - want)) if free else max(body, floor + 1)
        out.append((place_at, name))
        floor = place_at + max(len(name) + 1, MIN_GAP)
    return out


def fill(lines):
    """Достраивает аккорды в строках, где их нет. Возвращает (строки, что изменилось).

    Опорные — только строки с аккордами из источника, и отдельно для куплета
    и для припева: у припева своя гармония, и достраивать по нему куплет нельзя.
    Достроенные строки опорными не становятся — иначе на каждой следующей круг
    усыхал бы, и к концу куплета от него остался бы один аккорд.
    """
    out, refs, changes, gap, section = [], {}, [], 0, ''
    last = ''
    for raw in lines:
        if raw.startswith('---'):                 # новый вариант — свои опорные строки
            refs, gap, section = {}, 0, ''
            out.append(raw)
            continue
        if not raw.strip():                       # пустая строка — новый блок
            gap, section = 0, ''
            out.append(raw)
            continue
        lyric, chords = parse(raw)
        s = lyric.strip()
        if LABEL.match(s):                        # «Припев:» и прочие подписи
            section = s.split(':')[0].strip().lower()
            gap = 0
            out.append(raw)
            continue
        if not is_lyric(lyric):
            out.append(raw)
            continue
        if chords:
            refs[section] = (refs.get(section, []) + [(lyric, chords)])[-2:]
            last = section
            gap = 0
            out.append(raw)
            continue
        here = refs.get(section) or refs.get(last)
        if not here:                              # опереться не на что — не трогаем
            out.append(raw)
            continue
        # две опорные строки чередуются: первая строка куплета, вторая, первая...
        ref_lyric, ref_chords = here[gap % len(here)]
        if len(s) < SHORT:                        # короткая строка — только первый аккорд
            new = [(0, ref_chords[0][1])]
        else:
            new = spread(ref_lyric, ref_chords, lyric)
        out.append(place(lyric, new))
        changes.append(out[-1])
        gap += 1
    return out, changes


def body_start(lines):
    i = 0
    while i < len(lines) and lines[i].strip():
        i += 1
    return i


def show(raw):
    """Строка так, как её увидит человек: аккорды над текстом."""
    lyric, chords = parse(raw)
    row = [' '] * (max((c + len(n) for c, n in chords), default=0))
    for col, name in chords:
        row[col:col + len(name)] = name
    return ''.join(row).rstrip() + '\n' + lyric.rstrip()


def process(path, apply):
    lines = path.read_text(encoding='utf-8').split('\n')
    i = body_start(lines)
    body, changes = fill(lines[i:])
    if not changes:
        return 0
    print(f'\n=== {path.name}: достроено строк — {len(changes)}')
    for raw in changes:
        print(show(raw))
    if apply:
        path.write_text('\n'.join(lines[:i] + body), encoding='utf-8')
    return len(changes)


def main(args):
    apply = '--apply' in args
    targets = [Path(a) for a in args if a.endswith('.txt')] or sorted(SONGS.glob('*.txt'))
    total = sum(process(p, apply) for p in targets)
    if not total:
        print('Пропусков нет — аккорды есть в каждой строке.')
    elif not apply:
        print(f'\nВсего строк без аккордов: {total}. Записать: --apply')
    else:
        print(f'\nЗаписано. Достроено строк: {total}')


if __name__ == '__main__':
    main(sys.argv[1:])
