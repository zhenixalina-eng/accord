#!/usr/bin/env python3
"""Проверяет, нет ли такой песни в songs/ — по названию и по самому тексту.

Название и исполнитель могут быть записаны иначе («31 весна» / «31-я весна»),
поэтому главная проверка — по строкам текста без аккордов и знаков.

Запуск:  python3 tools/check_duplicate.py "Асфальт" "Я по асфальту шагаю"
Второй аргумент — любая строка текста песни, лучше из припева.
"""
import re
import sys
from pathlib import Path

SONGS = Path(__file__).resolve().parent.parent / 'songs'


def strip_chords(line):
    return re.sub(r'\[[^\]]*\]', '', line)


def normalize(s):
    s = strip_chords(s).lower().replace('ё', 'е')
    return re.sub(r'[^a-zа-я0-9 ]', ' ', s).split()


def song_parts(path):
    lines = path.read_text(encoding='utf-8').split('\n')
    meta, i = {}, 0
    while i < len(lines) and lines[i].strip():
        m = re.match(r'^(\w+):\s*(.*)$', lines[i])
        if m:
            meta[m[1]] = m[2].strip()
        i += 1
    body = [strip_chords(l).strip() for l in lines[i:] if l.strip()]
    return meta.get('title', ''), meta.get('artist', ''), body


def main(title, line=None):
    want_title = ' '.join(normalize(title))
    want_line = ' '.join(normalize(line)) if line else None

    hits = []
    for path in sorted(SONGS.glob('*.txt')):
        have_title, artist, body = song_parts(path)
        reasons = []
        if ' '.join(normalize(have_title)) == want_title:
            reasons.append('совпало название')
        if want_line and len(want_line.split()) >= 3:
            for l in body:
                norm = ' '.join(normalize(l))
                # короткие строки («У», «И») совпадают с чем угодно — не считаем
                if len(norm.split()) < 3:
                    continue
                if want_line in norm or norm in want_line:
                    reasons.append(f'совпала строка: «{l}»')
                    break
        if reasons:
            hits.append((path.name, have_title, artist, reasons))

    if not hits:
        print(f'Дублей нет — «{title}» можно добавлять новым файлом.')
        return
    print('НАЙДЕН ДУБЛЬ — добавлять надо вариантом в существующий файл:')
    for name, have_title, artist, reasons in hits:
        print(f'  songs/{name} — «{have_title}» ({artist})')
        for r in reasons:
            print(f'      {r}')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit('укажи название песни и, по возможности, строку текста')
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
