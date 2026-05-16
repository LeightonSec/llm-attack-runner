import json
import os
import pytest

from report import generate_report, save_report, _sanitise_target


def _make_result(verdict, category='jailbreak'):
    return {
        'id': 'jb_001', 'name': 'Test', 'category': category,
        'technique': 'test', 'payload': 'ignore rules',
        'response': 'Sure!', 'status_code': 200,
        'error': None, 'verdict': verdict,
    }


class TestSanitiseTarget:
    def test_strips_query_params(self):
        url = 'https://example.com/chat?token=secret&user=admin'
        assert 'token' not in _sanitise_target(url)
        assert 'secret' not in _sanitise_target(url)

    def test_strips_fragment(self):
        url = 'https://example.com/chat#section'
        assert '#' not in _sanitise_target(url)

    def test_preserves_path(self):
        url = 'https://example.com/api/chat'
        assert _sanitise_target(url) == 'https://example.com/api/chat'

    def test_handles_malformed(self):
        result = _sanitise_target("not-a-url")
        assert isinstance(result, str)


class TestGenerateReport:
    def test_empty_results_no_division_error(self):
        report = generate_report([])
        assert report['summary']['total_payloads'] == 0
        assert report['summary']['fold_rate'] == 0.0

    def test_fold_rate_calculation(self):
        results = [
            _make_result('FOLD'),
            _make_result('PARTIAL'),
            _make_result('RESIST'),
            _make_result('RESIST'),
        ]
        report = generate_report(results)
        assert report['summary']['fold_rate'] == pytest.approx(0.5)

    def test_all_resist(self):
        results = [_make_result('RESIST')] * 5
        report = generate_report(results)
        assert report['summary']['fold_rate'] == 0.0
        assert report['summary']['resist'] == 5

    def test_bypasses_only_fold_and_partial(self):
        results = [
            _make_result('FOLD'),
            _make_result('PARTIAL'),
            _make_result('RESIST'),
            _make_result('UNCLEAR'),
        ]
        report = generate_report(results)
        assert len(report['bypasses']) == 2
        assert all(r['verdict'] in ('FOLD', 'PARTIAL') for r in report['bypasses'])

    def test_by_category_counts(self):
        results = [
            _make_result('FOLD', 'jailbreak'),
            _make_result('RESIST', 'jailbreak'),
            _make_result('FOLD', 'prompt_injection'),
        ]
        report = generate_report(results)
        assert report['by_category']['jailbreak']['total'] == 2
        assert report['by_category']['prompt_injection']['total'] == 1

    def test_target_sanitised_in_output(self):
        report = generate_report([], target='https://example.com/chat?secret=abc')
        assert 'secret' not in report['target']

    def test_generated_at_present(self):
        report = generate_report([])
        assert 'generated_at' in report
        assert report['generated_at']


class TestSaveReport:
    def test_saves_valid_json(self, tmp_path):
        report = generate_report([_make_result('RESIST')])
        out = str(tmp_path / 'test_report.json')
        path = save_report(report, output_path=out)
        assert os.path.exists(path)
        with open(path) as f:
            loaded = json.load(f)
        assert loaded['summary']['total_payloads'] == 1

    def test_auto_generates_filename(self, tmp_path, monkeypatch):
        monkeypatch.setattr('report.RESULTS_DIR', str(tmp_path))
        report = generate_report([])
        path = save_report(report)
        assert os.path.exists(path)
        assert 'redteam_' in os.path.basename(path)
