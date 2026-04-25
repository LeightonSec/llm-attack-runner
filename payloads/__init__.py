import json
import os

PAYLOAD_DIR = os.path.dirname(__file__)


def load_payloads(category: str) -> list:
    path = os.path.join(PAYLOAD_DIR, f'{category}.json')
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return json.load(f)


def load_all_payloads(categories: list) -> list:
    result = []
    for cat in categories:
        result.extend(load_payloads(cat))
    return result
