"""
Whisper Speech-to-Text Transcriber.

Uses faster-whisper for efficient CPU inference with int8 quantisation.
Model size is configurable via environment variable WHISPER_MODEL_SIZE.

Install: pip install faster-whisper
"""

import os
import logging

logger = logging.getLogger(__name__)

# Lazy-loaded model
_whisper_model = None


def _get_model(model_size: str = None):
    global _whisper_model
    if _whisper_model is None:
        try:
            from faster_whisper import WhisperModel
            size = model_size or os.environ.get("WHISPER_MODEL_SIZE", "medium")
            _whisper_model = WhisperModel(
                size,
                device="cpu",       # change to "cuda" if GPU available
                compute_type="int8" # quantised for CPU speed
            )
            logger.info(f"Loaded Whisper model (size={size}, int8)")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise
    return _whisper_model


class WhisperTranscriber:
    """
    Model: faster-whisper medium (good balance of speed and accuracy on CPU)
    Falls back to 'small' if memory is constrained.

    Install: pip install faster-whisper
    """

    def __init__(self, model_size: str = None):
        self.model_size = model_size or os.environ.get("WHISPER_MODEL_SIZE", "medium")

    def transcribe(self, audio_path: str) -> list[dict]:
        """
        Input:  path to a .wav file (16kHz mono PCM)
        Output: list of segments
        [
            {"start": 0.0, "end": 2.4, "text": "Let's talk about the budget.", "confidence": 0.93},
            ...
        ]
        """
        model = _get_model(self.model_size)
        try:
            segments, info = model.transcribe(audio_path, beam_size=5)
            results = []
            for seg in segments:
                results.append({
                    "start": seg.start,
                    "end": seg.end,
                    "text": seg.text.strip(),
                    "confidence": getattr(seg, "avg_logprob", 0.0),
                })
            logger.info(f"Transcribed {audio_path}: {len(results)} segments, lang={info.language}")
            return results
        except Exception as e:
            logger.error(f"Transcription failed for {audio_path}: {e}")
            raise
