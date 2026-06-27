#!/usr/bin/env python3
"""
LLM Red Team Tool — adversarial prompt testing for authorised targets only.
Never use against systems you do not own or have explicit written permission to test.
"""
import argparse
import sys
from urllib.parse import urlparse

from report import generate_report, save_report
from runner import run_campaign

CATEGORIES = [
    'jailbreak',
    'prompt_injection',
    'data_extraction',
    'social_engineering',
    'reconnaissance',
]


def confirm_target(target_url: str) -> bool:
    hostname = urlparse(target_url).netloc or target_url

    print()
    print('=' * 62)
    print('  LLM RED TEAM TOOL  —  AUTHORISED TESTING ONLY')
    print('=' * 62)
    print(f'  Target : {target_url}')
    print()
    print('  Only proceed if you own or have explicit written')
    print('  authorisation to test this target.')
    print()
    try:
        entered = input(f'  Type the hostname to confirm [{hostname}]: ').strip()
    except (KeyboardInterrupt, EOFError):
        return False

    return entered == hostname


def print_summary(report: dict, output_path: str) -> None:
    s = report['summary']
    print()
    print('=' * 62)
    print('  RESULTS')
    print('=' * 62)

    for cat, stats in report['by_category'].items():
        t       = stats['total']
        folds   = stats['fold']
        partial = stats['partial']
        resists = stats['resist']
        bar     = '█' * folds + '▒' * partial + '░' * resists + '·' * (t - folds - partial - resists)
        print(f'  {cat:<22}  {bar:<14}  {folds + partial}/{t} bypassed')

    print()
    print(f'  Fold rate   : {s["fold_rate"]:.0%}  '
          f'({s["fold"]} fold, {s["partial"]} partial, '
          f'{s["resist"]} resist, {s["unclear"]} unclear)')

    if report['bypasses']:
        print()
        print('  Bypasses:')
        for b in report['bypasses']:
            print(f'    [{b["verdict"]:7s}] {b["id"]:10s}  {b["name"]}')

    print()
    print(f'  Full results: {output_path}')
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog='python cli.py',
        description='LLM Red Team Tool — adversarial prompt testing',
        epilog='Only use against systems you own or have explicit authorisation to test.',
    )
    parser.add_argument('--target', required=True,
                        help='Target URL  e.g. http://localhost:5001/chat')
    parser.add_argument('--category', choices=CATEGORIES + ['all'], default='all',
                        help='Attack category (default: all)')
    parser.add_argument('--delay', type=float, default=1.0,
                        help='Seconds between requests (default: 1.0)')
    parser.add_argument('--request-field', default='prompt',
                        help='JSON body field for the prompt (default: prompt)')
    parser.add_argument('--response-field', default='response',
                        help='JSON response field to read (default: response)')
    parser.add_argument('--header', action='append', dest='headers', default=[],
                        metavar='KEY:VALUE',
                        help='Extra request header, repeatable  e.g. --header "X-API-Key:abc"')
    parser.add_argument('--output',
                        help='Save results to this path (default: results/redteam_<ts>.json)')
    parser.add_argument('--dry-run', action='store_true',
                        help='List payloads without sending any requests')
    parser.add_argument('--yes', action='store_true',
                        help='Skip confirmation prompt (for authorised CI pipelines only)')

    args = parser.parse_args()

    # Parse extra headers
    extra_headers: dict = {}
    for h in args.headers:
        if ':' not in h:
            print(f'Error: bad header "{h}" — use KEY:VALUE format', file=sys.stderr)
            sys.exit(1)
        k, v = h.split(':', 1)
        extra_headers[k.strip()] = v.strip()

    categories = CATEGORIES if args.category == 'all' else [args.category]

    # Dry run — just list payloads
    if args.dry_run:
        from payloads import load_payloads
        total = 0
        for cat in categories:
            ps = load_payloads(cat)
            total += len(ps)
            print(f'\n[{cat}] — {len(ps)} payloads')
            for p in ps:
                print(f'  {p["id"]:10s}  {p["technique"]:24s}  {p["name"]}')
        print(f'\nTotal: {total} payloads')
        return

    # Authorisation gate
    if not args.yes and not confirm_target(args.target):
        print('\nAborted.')
        sys.exit(0)

    print(f'\n  Target     : {args.target}')
    print(f'  Categories : {", ".join(categories)}')
    print(f'  Delay      : {args.delay}s')
    print()

    results     = run_campaign(
        target         = args.target,
        categories     = categories,
        delay          = args.delay,
        request_field  = args.request_field,
        response_field = args.response_field,
        extra_headers  = extra_headers,
    )
    report      = generate_report(results, target=args.target)
    output_path = save_report(report, args.output)

    print_summary(report, output_path)


if __name__ == '__main__':
    main()
