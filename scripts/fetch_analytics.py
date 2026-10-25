"""Fetch only aggregated game-performance dimensions from GA4, never raw events."""
import argparse
import json
import urllib.error
import urllib.request
from performance_data import build_snapshot, save_snapshot

DIMENSIONS = ['customEvent:hardware_model', 'customEvent:game_name', 'customEvent:game_id',
              'customEvent:execution_mode', 'customEvent:thermal_state']
METRICS = ['customEvent:fps_measured_seconds', 'customEvent:fps_frame_equivalents']


def request_body(start, end, offset=0):
    return dict(dateRanges=[dict(startDate=start, endDate=end)],
                dimensions=[dict(name=name) for name in DIMENSIONS],
                metrics=[dict(name=name) for name in METRICS],
                dimensionFilter=dict(filter=dict(fieldName='eventName',
                    stringFilter=dict(matchType='EXACT', value='game_performance'))),
                orderBys=[dict(dimension=dict(dimensionName=name)) for name in DIMENSIONS],
                limit=10000, offset=offset, keepEmptyRows=False)


def fetch_snapshot(post, start, end):
    records, offset = [], 0
    while True:
        response = post(request_body(start, end, offset))
        metadata = response.get('metadata', {})
        # Missing rows cannot safely be interpreted as missing measurements.
        if metadata.get('subjectToThresholding') or metadata.get('dataLossFromOtherRow') or metadata.get('samplingMetadatas'):
            raise ValueError('GA returned thresholded, sampled, or incomplete aggregates; keeping last good snapshot')
        dimensions = [d['name'] for d in response.get('dimensionHeaders', [])]
        metrics = [m['name'] for m in response.get('metricHeaders', [])]
        if dimensions != DIMENSIONS or metrics != METRICS:
            raise ValueError('Unexpected GA response schema')
        rows = response.get('rows', [])
        for row in rows:
            values = [v['value'] for v in row['dimensionValues']]
            measured = [v['value'] for v in row['metricValues']]
            if len(values) != 5 or len(measured) != 2:
                raise ValueError('Incomplete GA row')
            records.append((*values, *measured))
        offset += len(rows)
        if offset >= int(response.get('rowCount', 0)):
            break
        if not rows or offset > 1000000:
            raise ValueError('GA pagination did not complete')
    return build_snapshot(records, start, end, 'Google Analytics Data API')


def reporting_period(days=None):
    if days is not None:
        if not 1 <= days <= 90:
            raise ValueError('Use 1–90 days, or omit --days for all available history')
        return dict(start=f'{days - 1}daysAgo', end='today', days=days,
                    label=f'{days}-day window through today (property timezone)')
    # Predates GA4 and this property's collection; no rolling cutoff excludes older data.
    return dict(start='2015-08-14', end='today',
                label='All available history through today (property timezone)')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--property', default='558536976')
    parser.add_argument('--output', default='docs/data/performance.json')
    parser.add_argument('--days', type=int, help='Optional rolling window; default: all available history')
    args = parser.parse_args()
    if not args.property.isdigit():
        parser.error('Use a numeric property')
    try:
        period = reporting_period(args.days)
    except ValueError as error:
        parser.error(str(error))
    import google.auth
    from google.auth.transport.requests import Request
    credentials, _ = google.auth.default(scopes=['https://www.googleapis.com/auth/analytics.readonly'])
    credentials.refresh(Request())
    # Query relative dates so GA uses the property's timezone, including today's partial data.
    start, end = period['start'], period['end']
    def post(body):
        request = urllib.request.Request(
            f'https://analyticsdata.googleapis.com/v1beta/properties/{args.property}:runReport',
            data=json.dumps(body).encode(), method='POST',
            headers={'Authorization': f'Bearer {credentials.token}', 'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            # Do not print credentials, full HTTP requests or response payloads.
            raise RuntimeError(f'Analytics API HTTP {error.code}. Check Viewer access, API enablement, and registered custom fields.') from None
    snapshot = fetch_snapshot(post, start, end)
    # Relative period labels are explicit rather than guessing the property timezone.
    snapshot['period'] = period
    save_snapshot(snapshot, args.output)
    print(f'Updated {len(snapshot["rows"])} aggregate rows')


if __name__ == '__main__':
    main()
