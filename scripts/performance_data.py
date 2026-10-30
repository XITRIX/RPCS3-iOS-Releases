"""Shared, validated public aggregate format. Never accepts user/session identifiers."""
import json
import math
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

STATES = ('nominal', 'fair', 'serious', 'critical', 'unknown')


def number(value):
    result = float(value)
    if not math.isfinite(result) or result < 0:
        raise ValueError('Metrics must be finite, nonnegative numbers')
    return result


def build_snapshot(records, start, end, source, warnings=None):
    groups = {}
    for record in records:
        device, game, title, mode, thermal, seconds, frames = record
        # AOT is still in development; do not publish its measurements or mix them into other modes.
        if mode == 'aot':
            continue
        if mode not in ('jit', 'interpreter') or thermal not in STATES:
            raise ValueError('Unknown execution mode or thermal state')
        if not all(isinstance(v, str) and v.strip() and len(v) <= 150 for v in (device, game, title)):
            raise ValueError('Missing or invalid game/device identity')
        seconds, frames = number(seconds), number(frames)
        if not seconds:
            if frames:
                raise ValueError('Frames without measured duration')
            continue
        key = (device, game, title, mode)
        group = groups.setdefault(key, dict(device=device, game=game, titleId=title, mode=mode, thermal={}))
        cell = group['thermal'].setdefault(thermal, dict(seconds=0, frameEquivalents=0))
        cell['seconds'] += seconds
        cell['frameEquivalents'] += frames
    if not groups:
        raise ValueError('No usable measurements; keep the last good snapshot')
    rows = sorted(groups.values(), key=lambda row: (row['game'].casefold(), row['device'], row['mode']))
    return dict(schemaVersion=1, generatedAt=datetime.now(timezone.utc).isoformat(timespec='seconds'),
                period=dict(start=start, end=end), source=source, warnings=warnings or [], rows=rows)


def save_snapshot(snapshot, output):
    """An interrupted download must never replace the last valid publication."""
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(snapshot, ensure_ascii=False, indent=2, allow_nan=False) + '\n'
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as temp:
        temp.write(content)
        name = temp.name
    os.replace(name, path)
