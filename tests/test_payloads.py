import pytest
from payloads import load_payloads, load_all_payloads

KNOWN_CATEGORIES = ['jailbreak', 'prompt_injection', 'data_extraction',
                    'social_engineering', 'reconnaissance']


class TestLoadPayloads:
    @pytest.mark.parametrize("category", KNOWN_CATEGORIES)
    def test_known_category_returns_list(self, category):
        result = load_payloads(category)
        assert isinstance(result, list)
        assert len(result) > 0

    @pytest.mark.parametrize("category", KNOWN_CATEGORIES)
    def test_payloads_have_required_fields(self, category):
        for p in load_payloads(category):
            assert 'id' in p
            assert 'name' in p
            assert 'payload' in p
            assert 'category' in p
            assert p['category'] == category

    def test_unknown_category_returns_empty(self):
        assert load_payloads('nonexistent') == []

    def test_payload_text_is_nonempty(self):
        for p in load_payloads('jailbreak'):
            assert p['payload'].strip()


class TestLoadAllPayloads:
    def test_combines_multiple_categories(self):
        jailbreak = load_payloads('jailbreak')
        injection = load_payloads('prompt_injection')
        combined = load_all_payloads(['jailbreak', 'prompt_injection'])
        assert len(combined) == len(jailbreak) + len(injection)

    def test_single_category_matches_load_payloads(self):
        assert load_all_payloads(['jailbreak']) == load_payloads('jailbreak')

    def test_empty_categories_returns_empty(self):
        assert load_all_payloads([]) == []

    def test_unknown_category_skipped(self):
        result = load_all_payloads(['jailbreak', 'nonexistent'])
        assert result == load_payloads('jailbreak')
