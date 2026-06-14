"""Tests for single-message song delivery helpers."""
from io import BytesIO

from app.services.song_pipeline import (
    CAPTION_LIMIT,
    build_song_caption,
    _make_thumbnail,
)


def test_caption_includes_title_style_lyrics():
    cap = build_song_caption("Saturday", "indie folk", "[Verse]\nla la la")
    assert "Saturday" in cap
    assert "indie folk" in cap
    assert "la la la" in cap


def test_caption_truncates_long_lyrics():
    long_lyrics = "ля " * 2000  # ~6000 chars
    cap = build_song_caption("T", "S", long_lyrics)
    assert len(cap) <= CAPTION_LIMIT
    assert cap.endswith("…")


def test_caption_without_lyrics():
    cap = build_song_caption("T", "S", None)
    assert "T" in cap and "S" in cap


def test_caption_escapes_html():
    cap = build_song_caption("a<b>c", None, "x & y < z")
    assert "&lt;b&gt;" in cap
    assert "&amp;" in cap


def test_make_thumbnail_resizes_to_jpeg():
    from PIL import Image

    # 1000x1000 PNG -> should come back as a small JPEG within limits.
    src = Image.new("RGB", (1000, 1000), (10, 120, 200))
    buf = BytesIO()
    src.save(buf, format="PNG")
    out = _make_thumbnail(buf.getvalue())
    assert out is not None
    assert len(out) <= 200_000
    # verify it's a valid JPEG ≤320px
    thumb = Image.open(BytesIO(out))
    assert thumb.format == "JPEG"
    assert max(thumb.size) <= 320


def test_make_thumbnail_bad_bytes_returns_none():
    assert _make_thumbnail(b"not an image") is None


def test_lyrics_quote_is_expandable_blockquote():
    from app.services.song_pipeline import _lyrics_quote

    q = _lyrics_quote("[Verse]\nline one\nline two")
    assert q.startswith("<blockquote expandable>")
    assert q.endswith("</blockquote>")
    assert "line one" in q


def test_lyrics_quote_truncates_long():
    from app.services.song_pipeline import _lyrics_quote

    q = _lyrics_quote("x" * 9000)
    # capped well under Telegram's 4096-char message limit
    assert len(q) < 4096


def test_photo_caption_has_title_style_and_quoted_lyrics():
    from app.services.song_pipeline import build_photo_caption

    cap = build_photo_caption("Тяжёлая судьба", "depressive rock", "[Verse]\nтекст")
    assert "Тяжёлая судьба" in cap
    assert "depressive rock" in cap
    assert "<blockquote expandable>" in cap
    assert "текст" in cap


def test_photo_caption_within_limit():
    from app.services.song_pipeline import build_photo_caption, CAPTION_LIMIT

    cap = build_photo_caption("T", "S", "ля " * 2000)
    assert len(cap) <= CAPTION_LIMIT
    assert cap.endswith("</blockquote>")
