"""
test_voice.py — Phase 4 tests for voice transcription.
Covers error handling: transcription failure falls back gracefully,
never crashes.
"""
from app.voice import transcribe_audio


def test_transcribe_garbage_bytes_fails_gracefully():
    """
    Uploading non-audio bytes should return a clean error dict,
    never raise an exception (gap-fix: error handling).
    """
    garbage_bytes = b"this is not real audio data at all"
    result = transcribe_audio(garbage_bytes, "fake.webm")

    assert isinstance(result, dict)
    assert "success" in result
    assert "text" in result
    assert "error" in result
    assert result["success"] is False
    assert result["error"] is not None


def test_transcribe_empty_bytes_fails_gracefully():
    """Empty audio should be handled without crashing."""
    result = transcribe_audio(b"", "empty.webm")
    assert isinstance(result, dict)
    assert result["success"] is False