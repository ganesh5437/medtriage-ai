"""
voice.py — Voice transcription via OpenAI Whisper (local, offline).
Model size pinned to "base". Model loaded once at import time.
"""
import logging
import tempfile
import os

logger = logging.getLogger("medtriage.voice")

_whisper_model = None
_MODEL_SIZE = "base"


def _get_model():
    global _whisper_model
    if _whisper_model is None:
        try:
            import whisper
            logger.info("Loading Whisper model (%s)...", _MODEL_SIZE)
            _whisper_model = whisper.load_model(_MODEL_SIZE)
            logger.info("Whisper model loaded.")
        except Exception as exc:
            logger.error("Failed to load Whisper model: %s", exc)
            raise
    return _whisper_model


def transcribe_audio(audio_bytes: bytes, filename: str = "audio.webm") -> dict:
    tmp_path = None
    try:
        model = _get_model()
        suffix = os.path.splitext(filename)[1] or ".webm"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        result = model.transcribe(tmp_path, fp16=False)
        text = result.get("text", "").strip()

        if not text:
            return {
                "success": False,
                "text": "",
                "error": "No speech detected in the recording. Please try again or type your message.",
            }

        return {"success": True, "text": text, "error": None}

    except Exception as exc:
        logger.error("Whisper transcription failed: %s", exc)
        return {
            "success": False,
            "text": "",
            "error": "Voice unavailable. Please type your message.",
        }
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass