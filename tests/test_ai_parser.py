"""
Tests for the LLM response parser/validator.
"""

import pytest
from app.ai.parser import parse_suggestions, ParseError


def test_valid_response_parses_correctly():
    raw = '{"suggestions": [{"prerequisite_id": 1, "evidence": "after foundation", "reason": "needs it", "confidence": 90}]}'
    result = parse_suggestions(raw, valid_task_ids={1, 2, 3})
    assert len(result) == 1
    assert result[0]["prerequisite_id"] == 1
    assert result[0]["confidence"] == 90


def test_empty_suggestions_list():
    raw = '{"suggestions": []}'
    result = parse_suggestions(raw, valid_task_ids={1, 2, 3})
    assert result == []


def test_strips_markdown_fences():
    raw = '```json\n{"suggestions": []}\n```'
    result = parse_suggestions(raw, valid_task_ids={1})
    assert result == []


def test_hallucinated_task_id_is_dropped():
    # prerequisite_id 999 doesn't exist in valid_task_ids -- must be filtered out.
    raw = '{"suggestions": [{"prerequisite_id": 999, "evidence": "x", "reason": "y", "confidence": 80}]}'
    result = parse_suggestions(raw, valid_task_ids={1, 2, 3})
    assert result == []


def test_out_of_range_confidence_is_dropped():
    raw = '{"suggestions": [{"prerequisite_id": 1, "evidence": "x", "reason": "y", "confidence": 150}]}'
    result = parse_suggestions(raw, valid_task_ids={1})
    assert result == []


def test_malformed_entry_is_skipped_but_others_kept():
    raw = """{"suggestions": [
        {"prerequisite_id": 1, "evidence": "good", "reason": "valid one", "confidence": 90},
        {"prerequisite_id": "not-an-int", "evidence": "bad", "reason": "invalid", "confidence": 50}
    ]}"""
    result = parse_suggestions(raw, valid_task_ids={1, 2})
    assert len(result) == 1
    assert result[0]["prerequisite_id"] == 1


def test_completely_invalid_json_raises():
    raw = "this is not json at all { broken"
    with pytest.raises(ParseError):
        parse_suggestions(raw, valid_task_ids={1})


def test_missing_suggestions_key_raises():
    raw = '{"foo": "bar"}'
    with pytest.raises(ParseError):
        parse_suggestions(raw, valid_task_ids={1})
