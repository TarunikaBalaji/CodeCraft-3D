import json
import pytest
from core.meta_client import MetaAPIError, _extract_response_text


def test_extracts_responses_api_output_text():
    payload = {"output": [{"content": [{"type": "output_text", "text": '{"constraints": []}'}]}]}
    assert _extract_response_text(payload) == '{"constraints": []}'


def test_extracts_top_level_output_text():
    assert _extract_response_text({"output_text": "hello"}) == "hello"


def test_missing_text_raises_clear_error():
    with pytest.raises(MetaAPIError):
        _extract_response_text({"output": []})
