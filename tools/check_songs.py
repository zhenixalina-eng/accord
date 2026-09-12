#!/usr/bin/env python3
"""Общая проверка песенника: то, что легко не заметить глазом.

Что смотрит:
  • аккорды в строке не наезжают друг на друга (иначе на странице выйдет «EmC»);
  • аккорд не выходит за конец строки дальше, чем на свою длину, — такие хвосты
    бывают в подборах, но если аккорд улетел далеко, это обычно ошибка колонки;
  • у каждого аккорда есть аппликатура в index.html (иначе карточка скажет «нет схемы»);
  • в шапке есть title и artist;
  • файл записан в songs/index.json, а в index.json нет несуществующих файлов;
  • нет строк текста без аккордов (их достраивает tools/spread_chords.py).

Запуск:  python3 tools/check_songs.py
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from spread_chords import parse, fill, body_start

ROOT = Path(__file__).resolve().parent.parent
SONGS = ROOT / 'songs'
TAIL_SLACK = 4          # насколько аккорд может висеть за концом строки


FLAT_TO_SHARP = {'Db': 'C#', 'Eb': 'D#', 'Gb': 'F#', 'Ab': 'G#', 'Bb': 'A#'}


def shapes_from_page():
    """Аккорды, для которых в index.html есть аппликатуры (укулеле и гитара).

    Бемольные названия страница переводит в диезные сама, поэтому Bb считается
    известным, если известен A#.
    """
    text = (ROOT / 'index.html').read_text(encoding='utf-8')
    return set(re.findall(r"'([A-G][#b]?(?:m|m7|m6|dim|sus4|7)?)'\s*:\s*\[", text))


def known(chord, shapes):
    if chord in shapes:
        return True
    m = re.match(r'^([A-G]b)(.*)$', chord)
    return bool(m) and FLAT_TO_SHARP[m[1]] + m[2] in shapes


def base(chord):
    """«Am(V)» -> «Am»: подпись лада не мешает искать аппликатуру."""
    m = re.match(r'^(.*?)\(.+\)$', chord)
    return m[1] if m else chord


def check(path, shapes, registered):
    problems = []
    lines = path.read_text(encoding='utf-8').split('\n')
    i, meta = 0, {}
    while i < len(lines) and lines[i].strip():
        m = re.match(r'^(\w+):\s*(.*)$', lines[i])
        if m:
            meta[m[1]] = m[2].strip()
        i += 1
    for field in ('title', 'artist'):
        if not meta.get(field):
            problems.append(f'в шапке нет {field}')
    if path.name not in registered:
        problems.append('файла нет в songs/index.json')

    for n, raw in enumerate(lines[i:], start=i + 1):
        if raw.startswith('---'):
            continue
        lyric, chords = parse(raw)
        prev_end, prev_name = -1, ''
        for col, name in chords:
            if col < prev_end:
                problems.append(f'строка {n}: «{prev_name}» и «{name}» наезжают друг на друга')
            prev_end, prev_name = col + len(name) + 1, name
            if not known(base(name), shapes):
                problems.append(f'строка {n}: нет аппликатуры для «{name}»')
        if chords and chords[-1][0] > len(lyric) + TAIL_SLACK:
            problems.append(f'строка {n}: «{chords[-1][1]}» улетел за конец строки')
    # строки без аккордов, которые есть на что опереть: их достраивает spread_chords
    _, gaps = fill(lines[i:])
    for raw in gaps:
        lyric, _ = parse(raw)
        problems.append(f'без аккордов: «{lyric.strip()[:40]}» — достроит spread_chords.py')
    return problems


def main():
    index = json.loads((SONGS / 'index.json').read_text(encoding='utf-8'))
    registered = set(index)
    shapes = shapes_from_page()
    files = sorted(SONGS.glob('*.txt'))

    missing = [name for name in index if not (SONGS / name).exists()]
    bad = 0
    for name in missing:
        print(f'index.json: файла {name} нет на диске')
        bad += 1
    for path in files:
        problems = check(path, shapes, registered)
        if problems:
            bad += len(problems)
            print(f'\n{path.name}:')
            for p in problems:
                print(f'   {p}')
    print()
    if bad:
        print(f'Нашлось замечаний: {bad}')
    else:
        print(f'Проверено песен: {len(files)}. Всё чисто.')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
