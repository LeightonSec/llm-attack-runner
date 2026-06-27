from unittest.mock import MagicMock, patch

import requests

from runner import _fire


class TestFire:
    def _mock_response(self, status=200, json_data=None, text=''):
        mock = MagicMock()
        mock.status_code = status
        mock.text = text
        if json_data is not None:
            mock.json.return_value = json_data
        else:
            mock.json.side_effect = Exception("no json")
        return mock

    @patch('runner.requests.post')
    def test_success_extracts_response_field(self, mock_post):
        mock_post.return_value = self._mock_response(
            json_data={'response': 'I cannot help with that.'}
        )
        result = _fire('http://target/chat', 'test payload', 'prompt', 'response', {})
        assert result['status_code'] == 200
        assert result['response_text'] == 'I cannot help with that.'
        assert result['error'] is None

    @patch('runner.requests.post')
    def test_missing_response_field_returns_empty(self, mock_post):
        mock_post.return_value = self._mock_response(json_data={'other': 'value'})
        result = _fire('http://target/chat', 'test', 'prompt', 'response', {})
        assert result['response_text'] == ''

    @patch('runner.requests.post')
    def test_non_json_response_uses_text(self, mock_post):
        mock_post.return_value = self._mock_response(text='plain text response')
        result = _fire('http://target/chat', 'test', 'prompt', 'response', {})
        assert 'plain text response' in result['response_text']
        assert result['error'] is None

    @patch('runner.requests.post', side_effect=requests.exceptions.Timeout)
    def test_timeout_returns_error(self, _mock):
        result = _fire('http://target/chat', 'test', 'prompt', 'response', {})
        assert result['error'] == 'timeout'
        assert result['status_code'] is None

    @patch('runner.requests.post',
           side_effect=requests.exceptions.ConnectionError('refused'))
    def test_connection_error_returns_error(self, _mock):
        result = _fire('http://target/chat', 'test', 'prompt', 'response', {})
        assert result['error'].startswith('connection_error')
        assert result['status_code'] is None

    @patch('runner.requests.post')
    def test_extra_headers_passed_through(self, mock_post):
        mock_post.return_value = self._mock_response(json_data={'response': 'ok'})
        _fire('http://target/chat', 'test', 'prompt', 'response',
              {'X-Auth': 'token123'})
        _, kwargs = mock_post.call_args
        assert kwargs['headers']['X-Auth'] == 'token123'
