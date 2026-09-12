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
    """Картинки из сообщения, кроме тех, что внутри результатов инструментов.

    В результатах лежат мои же рендеры сайта. При этом сообщение, присланное
    посреди хода, может оказаться в одной записи с результатом инструмента —
    поэтому отбрасываем не всю запись, а только ветку tool_result.
    """
    if isinstance(node, dict):
        if node.get('type') == 'tool_result':
            return
        node = {k: v for k, v in node.items() if k != 'toolUseResult'}
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
            # Смотрим всю запись целиком: картинки из сообщений, присланных
            # посреди хода, лежат не в message, а в поле attachment.
            for media_type, data in images_in(rec):
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
