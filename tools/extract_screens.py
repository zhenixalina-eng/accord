#!/usr/bin/env python3
"""Вытаскивает картинки, присланные в чат, из транскрипта сессии Claude Code в screens/."""
import base64
import hashlib
import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
SESSIONS = Path.home() / '.claude' / 'projects' / '-Users-Evgeniya-dev-accord'
OUT = PROJECT / 'screens'


def images_in(node):
    if isinstance(node, dict):
        if node.get('type') == 'image':
            src = node.get('source') or {}
            if src.get('type') == 'base64' and src.get('data'):
                yield src['media_type'], src['data']
        for v in node.values():
            yield from images_in(v)
    elif isinstance(node, list):
        for v in node:
            yield from images_in(v)


def main():
    OUT.mkdir(exist_ok=True)
    transcripts = sorted(SESSIONS.glob('*.jsonl'), key=lambda p: p.stat().st_mtime, reverse=True)
    if not transcripts:
        sys.exit(f'нет транскриптов в {SESSIONS}')

    seen, saved = set(), []
    for t in transcripts:
        for line in t.open(encoding='utf-8'):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            msg = rec.get('message') or {}
            if msg.get('role') != 'user':
                continue
            # Результаты инструментов приходят с той же ролью «user» — в них лежат
            # картинки, которые я сам же и отрендерил. Нужны только присланные в чат.
            content = msg.get('content')
            if isinstance(content, list) and any(
                isinstance(b, dict) and b.get('type') == 'tool_result' for b in content
            ):
                continue
            for media_type, data in images_in(msg):
                raw = base64.b64decode(data)
                digest = hashlib.sha1(raw).hexdigest()[:10]
                if digest in seen:
                    continue
                seen.add(digest)
                ext = {'image/png': 'png', 'image/jpeg': 'jpg', 'image/webp': 'webp'}.get(media_type, 'png')
                ts = (rec.get('timestamp') or '').replace(':', '-')[:19] or 'unknown'
                path = OUT / f'{ts}_{digest}.{ext}'
                if not path.exists():
                    path.write_bytes(raw)
                saved.append((path, len(raw)))

    if not saved:
        print('картинок в транскриптах не найдено')
        return
    for path, size in saved:
        print(f'{path.relative_to(PROJECT)}  {size // 1024} KB')


if __name__ == '__main__':
    main()
