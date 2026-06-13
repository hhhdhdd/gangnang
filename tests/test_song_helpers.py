"""Pure-function unit tests for the song pipeline + schedule helpers.

No DB / network — these cover the parsing and formatting logic that's
easy to get subtly wrong (JSON unwrapping, field clamping, cron<->HH:MM).
"""
import pytest

from app.services.song_pipeline import (
    SongPipelineError,
    build_chat_text,
    trim_chat_text,
    _parse_song_draft,
    _tolerant_json_parse,
)
from app.handlers.song_admin import _cron_to_hhmm


class _Msg:
    def __init__(self, username, full_name, text, user_id=1):
        self.username = username
        self.full_name = full_name
        self.text = text
        self.user_id = user_id


def test_build_chat_text_formats_and_skips_empty():
    msgs = [
        _Msg("alice", None, "hi there"),
        _Msg(None, "Bob B", "line two"),
        _Msg(None, None, "   ", 3),          # blank -> skipped
        _Msg("c", "C", "multi\nline"),       # newline flattened
    ]
    out = build_chat_text(msgs)
    assert out == "@alice: hi there\n@Bob B: line two\n@c: multi line"


def test_build_chat_text_anon_user_fallback():
    out = build_chat_text([_Msg(None, None, "yo", 42)])
    assert out == "@user42: yo"


def test_trim_chat_text_keeps_tail():
    assert trim_chat_text("abcdefgh", 4) == "efgh"
    assert trim_chat_text("short", 100) == "short"


@pytest.mark.parametrize(
    "raw,expected",
    [
        ('```json\n{"a": 1}\n```', {"a": 1}),
        ("```\n{\"b\": 2}\n```", {"b": 2}),
        ('json {"c": 3}', {"c": 3}),
        ('{"d": 4}', {"d": 4}),
        ("not json at all", None),
    ],
)
def test_tolerant_json_parse(raw, expected):
    assert _tolerant_json_parse(raw) == expected


def test_parse_song_draft_clamps_and_defaults():
    d = _parse_song_draft(
        {"title": "T", "style": "S", "lyrics": "L", "summary": "X"}
    )
    assert (d.title, d.style, d.lyrics, d.summary) == ("T", "S", "L", "X")
    # summary optional
    d2 = _parse_song_draft({"title": "T", "style": "S", "lyrics": "L"})
    assert d2.summary == ""


@pytest.mark.parametrize("missing", [{"title": "x"}, {"style": "x"}, {}])
def test_parse_song_draft_rejects_missing_required(missing):
    with pytest.raises(SongPipelineError) as ei:
        _parse_song_draft(missing)
    assert ei.value.code == "llm_invalid_draft"


def test_parse_song_draft_rejects_non_dict():
    with pytest.raises(SongPipelineError):
        _parse_song_draft(["not", "a", "dict"])


@pytest.mark.parametrize(
    "cron,expected",
    [
        ("0 21 * * *", "21:00"),
        ("30 9 * * *", "09:30"),
        (None, None),
        ("* *", None),
        ("bad", None),
    ],
)
def test_cron_to_hhmm(cron, expected):
    assert _cron_to_hhmm(cron) == expected
