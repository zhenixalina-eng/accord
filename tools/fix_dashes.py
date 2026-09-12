#!/usr/bin/env python3
"""Приводит тире и дефисы в текстах песен к правилам русской типографики.

Дефис пишется внутри слова без пробелов (кто-то, смотри-ка), тире — между
словами с пробелами и длинное (—). В распознанных текстах это перемешано:
дефис стоит вместо тире, а составные слова разорваны на два («кто – то»).

Аккорды не пострадают: они записаны прямо в тексте ([Am]) и остаются
приклеенными к своей букве, даже если слово рядом стало короче.

Запуск:  python3 tools/fix_dashes.py [--apply]
Без --apply только показывает, что изменится.
"""
import glob
import re
import sys

DASH = r'[-–—]'

# Частицы, которые пишутся через дефис и часто оказываются оторванными
PARTICLES = r'(то|либо|нибудь|ка|таки)'

RULES = [
    # разорванные составные слова: «кто – то» → «кто-то»
    (re.compile(rf'(\w)\s*{DASH}\s*{PARTICLES}\b'), r'\1-\2'),
    (re.compile(rf'\b(кое)\s*{DASH}\s*(\w)'), r'\1-\2'),
    (re.compile(rf'\b(из)\s*{DASH}\s*(за|под)\b'), r'\1-\2'),
    # тире между словами — длинное
    (re.compile(rf'(?<=\s){DASH}(?=\s)'), '—'),
    # тире в конце строки
    (re.compile(rf'(\S)\s+{DASH}\s*$'), r'\1 —'),
    # тире в начале строки (реплика)
    (re.compile(rf'^(\s*){DASH}\s+'), r'\1— '),
]


def fix_line(line):
    for pattern, repl in RULES:
        line = pattern.sub(repl, line)
    return line


def main():
    apply = '--apply' in sys.argv
    changed_files = 0
    changed_lines = 0

    for path in sorted(glob.glob('songs/*.txt')):
        out, touched = [], False
        for line in open(path, encoding='utf-8'):
            # строка-разделитель вариантов аккордов трогать нельзя
            new = line if line.startswith('---') else fix_line(line)
            if new != line:
                touched = True
                changed_lines += 1
                if not apply:
                    print(f'{path}:')
                    print(f'  было:  {line.rstrip()}')
                    print(f'  стало: {new.rstrip()}')
            out.append(new)
        if touched:
            changed_files += 1
            if apply:
                open(path, 'w', encoding='utf-8').write(''.join(out))

    action = 'Исправлено' if apply else 'Будет исправлено'
    print(f'\n{action}: строк {changed_lines}, файлов {changed_files}')
    if not apply:
        print('Запусти с --apply, чтобы записать.')


if __name__ == '__main__':
    main()
