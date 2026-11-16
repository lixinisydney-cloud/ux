"""Record A/B only from validated real output, preserving the separate C report."""
import argparse
import json
from pathlib import Path
from classify_notes import ClassificationError, load_dataset, read_json, validate_envelope, atomic_write, configure_console

ROOT = Path(__file__).resolve().parents[1]


def evaluate(result_path, report_path):
    notes, groups = load_dataset(ROOT / 'data/notes.json', ROOT / 'data/groups.json')
    report = read_json(report_path)
    raw = read_json(result_path)
    if isinstance(raw, dict) and raw.get('mode') == 'unavailable':
        report['realStatus'] = 'not_run_missing_api_key'
        report.pop('realProvenance', None)
        for case in report['cases']:
            case.update(realStatus=report['realStatus'], realOutput=None,
                        observedRealMemberships=None, passed=None)
    else:
        real = validate_envelope(raw, notes, groups, expected_mode='real')
        assignments = {row['noteId']: row for row in real['assignments']}
        report['realStatus'] = 'completed'
        report['realProvenance'] = {key: real[key] for key in
                                    ('model', 'generatedAt', 'datasetHash', 'promptVersion')}
        for case in report['cases']:
            row = assignments[case['noteId']]
            actual = [m['groupId'] for m in row['memberships']]
            case.update(realStatus='completed', realOutput=row,
                        observedRealMemberships=actual,
                        passed=set(case['humanExpectation']).issubset(actual))
    atomic_write(report_path, (json.dumps(report, ensure_ascii=False, indent=2) + '\n').encode())
    return report


def main():
    configure_console()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--result', type=Path, default=ROOT / 'data/classifications.real.json')
    parser.add_argument('--report', type=Path, default=ROOT / 'reports/cases-v07.json')
    args = parser.parse_args()
    try:
        report = evaluate(args.result, args.report)
    except (ClassificationError, KeyError, OSError):
        parser.exit(2, 'Cannot evaluate: expected valid data, report and real model result. No success was recorded.\n')
    print(json.dumps({'realStatus': report['realStatus'], 'cases': [
        {key: case[key] for key in ('case','realStatus','observedRealMemberships','passed')}
        for case in report['cases']]}, ensure_ascii=False, indent=2))
    if report['realStatus'] != 'completed':
        return 2
    return 0 if all(case['passed'] for case in report['cases']) else 1


if __name__ == '__main__':
    raise SystemExit(main())
