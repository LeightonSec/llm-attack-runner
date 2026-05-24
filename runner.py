import time
import requests
from payloads import load_all_payloads
from scorer import score_response

TIMEOUT = 15  # seconds per request


def _fire(target: str, payload_text: str, request_field: str,
          response_field: str, extra_headers: dict) -> dict:
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'LLMRedTeam/1.0 (authorized-testing)',
        **extra_headers,
    }
    try:
        resp = requests.post(  # gate: ignore — red team tool by design: fires attack payloads at authorised target LLM endpoints, documented in Gate 2 trust boundary map
            target,
            json={request_field: payload_text},
            headers=headers,
            timeout=TIMEOUT,
        )
        try:
            data = resp.json()
            text = data.get(response_field, '') if isinstance(data, dict) else str(data)
        except Exception:
            text = resp.text[:2000]

        return {'status_code': resp.status_code, 'response_text': str(text), 'error': None}

    except requests.exceptions.Timeout:
        return {'status_code': None, 'response_text': '', 'error': 'timeout'}
    except requests.exceptions.ConnectionError as e:
        return {'status_code': None, 'response_text': '', 'error': f'connection_error: {str(e)[:80]}'}
    except Exception as e:
        return {'status_code': None, 'response_text': '', 'error': f'error: {str(e)[:80]}'}


def run_campaign(target: str, categories: list, delay: float,
                 request_field: str, response_field: str,
                 extra_headers: dict) -> list:
    payloads = load_all_payloads(categories)
    results  = []

    SYMBOLS = {'FOLD': '✗', 'PARTIAL': '~', 'RESIST': '✓', 'UNCLEAR': '?', 'ERROR': '!'}

    for i, p in enumerate(payloads, 1):
        print(f'  [{i:3d}/{len(payloads)}] {p["id"]:10s}  {p["name"][:38]:<38}', end='  ', flush=True)

        raw = _fire(target, p['payload'], request_field, response_field, extra_headers)

        if raw['error']:
            verdict = 'ERROR'
        else:
            verdict = score_response(p['payload'], raw['response_text'])

        print(f'{SYMBOLS.get(verdict, "?")} {verdict}')

        results.append({
            'id':          p['id'],
            'name':        p['name'],
            'category':    p['category'],
            'technique':   p.get('technique', ''),
            'payload':     p['payload'],
            'response':    raw['response_text'],
            'status_code': raw['status_code'],
            'error':       raw['error'],
            'verdict':     verdict,
        })

        if i < len(payloads):
            time.sleep(delay)

    return results
