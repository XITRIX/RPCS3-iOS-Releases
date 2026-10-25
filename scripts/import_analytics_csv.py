"""Import a GA4 exploration CSV with paired duration / Average FPS columns."""
import argparse
import csv
import re
from pathlib import Path
from performance_data import STATES, build_snapshot, number, save_snapshot


def load_export(path, mode):
    text = Path(path).read_text(encoding='utf-8-sig')
    period = re.search(r'^# (\d{8})-(\d{8})\s*$', text, re.M)
    if not period:
        raise ValueError('Export must include its GA date-range comment')
    lines = list(csv.reader(line for line in text.splitlines() if line and not line.startswith('#')))
    thermal, columns = lines[0], lines[1]
    if columns[:3] != ['Hardware model', 'Game name', 'Game ID']:
        raise ValueError('Expected Hardware model, Game name, Game ID as rows')
    pairs = []
    for index, state in enumerate(thermal):
        if state in STATES and index + 1 < len(columns) and columns[index:index+2] == ['FPS measured seconds', 'Average FPS']:
            pairs.append((index, state))
    if not pairs:
        raise ValueError('No thermal duration / FPS column pairs found')
    records = []
    for row in lines[2:]:
        if not row or not row[0]:
            continue  # GA's total is not a device/game observation.
        for index, state in pairs:
            seconds, fps = number(row[index]), number(row[index+1])
            records.append((*row[:3], mode, state, seconds, seconds * fps))
    def date(value):
        return f'{value[:4]}-{value[4:6]}-{value[6:]}'
    return build_snapshot(records, date(period[1]), date(period[2]),
                          'Google Analytics exploration export')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv')
    parser.add_argument('--mode', required=True, choices=['jit', 'interpreter'])
    parser.add_argument('--output', default='docs/data/performance.json')
    args = parser.parse_args()
    snapshot = load_export(args.csv, args.mode)
    save_snapshot(snapshot, args.output)
    print(f'Imported {len(snapshot["rows"])} device/game/mode combinations')
