from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from performance_data import build_snapshot, number, save_snapshot
from fetch_analytics import DIMENSIONS, METRICS, fetch_snapshot, request_body, reporting_period
from import_analytics_csv import load_export


def response(rows, count=None, metadata=None):
    return dict(dimensionHeaders=[dict(name=x) for x in DIMENSIONS],
                metricHeaders=[dict(name=x) for x in METRICS],
                rows=[dict(dimensionValues=[dict(value=str(x)) for x in row[:5]],
                           metricValues=[dict(value=str(x)) for x in row[5:]]) for row in rows],
                rowCount=len(rows) if count is None else count, metadata=metadata or {})


class PerformanceDataTests(unittest.TestCase):
    def test_all_history_default_and_explicit_rolling_window(self):
        period = reporting_period()
        body = request_body(period['start'], period['end'])
        self.assertEqual(body['dateRanges'], [{'startDate': '2015-08-14', 'endDate': 'today'}])
        self.assertIn('All available history', period['label'])
        self.assertNotIn('days', period)
        self.assertEqual(reporting_period(30)['start'], '29daysAgo')
        for days in [0, 91]:
            with self.assertRaises(ValueError):
                reporting_period(days)

    def test_duration_weighting_zero_and_missing_are_distinct(self):
        rows = [('iPad16,3', 'Game', 'BLES00001', 'jit', 'nominal', 10, 600),
                ('iPad16,3', 'Game', 'BLES00001', 'jit', 'nominal', 90, 1800),
                ('iPad16,3', 'Game', 'BLES00001', 'jit', 'serious', 15, 0)]
        result = build_snapshot(rows, 'a', 'b', 'fixture')['rows'][0]
        self.assertEqual(result['thermal']['nominal'], dict(seconds=100, frameEquivalents=2400))
        self.assertEqual(result['thermal']['serious']['frameEquivalents'], 0)
        self.assertNotIn('critical', result['thermal'])

    def test_modes_remain_separate(self):
        rows = [('model', 'Game', 'ID', mode, 'fair', 60, 1800) for mode in ['jit', 'interpreter']]
        self.assertEqual(len(build_snapshot(rows, 'a', 'b', 'fixture')['rows']), 2)

    def test_invalid_and_empty_data_do_not_replace_snapshot(self):
        for value in ['nan', 'inf', '-1']:
            with self.assertRaises(ValueError): number(value)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'snapshot.json'
            output.write_text('last good')
            with self.assertRaises(ValueError):
                save_snapshot(build_snapshot([], 'a', 'b', 'fixture'), output)
            self.assertEqual(output.read_text(), 'last good')

    def test_pagination_and_metric_order(self):
        calls = []
        def post(body):
            calls.append(body)
            return response([('model', 'Game', 'ID', 'jit', 'nominal', 30, 900)], count=2)
        result = fetch_snapshot(post, '29daysAgo', 'today')
        self.assertEqual([body['offset'] for body in calls], [0, 1])
        self.assertEqual(result['rows'][0]['thermal']['nominal']['seconds'], 60)
        self.assertEqual(calls[0]['dimensionFilter']['filter']['stringFilter']['value'], 'game_performance')
        self.assertEqual(calls[0]['metrics'][1]['name'], 'customEvent:fps_frame_equivalents')

    def test_thresholded_and_partial_response_rejected(self):
        for metadata in [dict(subjectToThresholding=True), dict(dataLossFromOtherRow=True), dict(samplingMetadatas=[{}])]:
            with self.assertRaises(ValueError):
                fetch_snapshot(lambda _: response([], metadata=metadata), 'a', 'b')
        with self.assertRaises(ValueError):
            fetch_snapshot(lambda _: response([], count=1), 'a', 'b')

    def test_csv_thermal_column_order_and_totals(self):
        csv = '# 20261024-20261025\n,,Thermal state,serious,serious,nominal,nominal\nHardware model,Game name,Game ID,FPS measured seconds,Average FPS,FPS measured seconds,Average FPS\n,,,30,20,60,60\n"iPad16,3",Example,ID,30,20,0,0\n'
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'export.csv'; path.write_text(csv)
            snapshot = load_export(path, 'jit')
        self.assertEqual(snapshot['period'], dict(start='2026-10-24', end='2026-10-25'))
        self.assertEqual(len(snapshot['rows']), 1)
        self.assertEqual(snapshot['rows'][0]['thermal'], dict(serious=dict(seconds=30, frameEquivalents=600)))


if __name__ == '__main__': unittest.main()
