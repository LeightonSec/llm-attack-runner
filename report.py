import json
import os
from datetime import datetime, timezone
from urllib.parse import urlparse, urlunparse


def _sanitise_target(target: str) -> str:
    """Strip query params and fragments so auth tokens in URLs aren't saved to disk."""
    try:
        p = urlparse(target)
        return urlunparse((p.scheme, p.netloc, p.path, '', '', ''))
    except Exception:
        return target

RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'results')


def generate_report(results: list, target: str = '') -> dict:
    target = _sanitise_target(target)
    total      = len(results)
    by_verdict = {'FOLD': 0, 'PARTIAL': 0, 'RESIST': 0, 'UNCLEAR': 0, 'ERROR': 0}
    by_category: dict = {}

    for r in results:
        v   = r['verdict']
        cat = r['category']

        by_verdict[v] = by_verdict.get(v, 0) + 1

        if cat not in by_category:
            by_category[cat] = {'total': 0, 'fold': 0, 'partial': 0,
                                 'resist': 0, 'unclear': 0, 'error': 0}
        by_category[cat]['total'] += 1
        by_category[cat][v.lower()] = by_category[cat].get(v.lower(), 0) + 1

    folds     = by_verdict['FOLD'] + by_verdict['PARTIAL']
    fold_rate = folds / total if total > 0 else 0.0

    return {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'target':       target,
        'summary': {
            'total_payloads': total,
            'fold':           by_verdict['FOLD'],
            'partial':        by_verdict['PARTIAL'],
            'resist':         by_verdict['RESIST'],
            'unclear':        by_verdict['UNCLEAR'],
            'error':          by_verdict['ERROR'],
            'fold_rate':      fold_rate,
        },
        'by_category': by_category,
        'bypasses':    [r for r in results if r['verdict'] in ('FOLD', 'PARTIAL')],
        'all_results': results,
    }


def save_report(report: dict, output_path: str | None = None) -> str:
    os.makedirs(RESULTS_DIR, exist_ok=True)

    if not output_path:
        ts          = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        output_path = os.path.join(RESULTS_DIR, f'redteam_{ts}.json')

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)

    return output_path
