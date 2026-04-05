"""
Speaker Diarization using pyannote.audio.

Assigns a speaker label to each transcript segment.
Model: pyannote/speaker-diarization-3.1

ML Concepts:
- ECAPA-TDNN neural speaker embedding model
- Spectral clustering on cosine similarity matrix of embeddings
- Silhouette score used for optimal number of speakers
- Unsupervised clustering (connects to KNN/distance metric theme)
"""

import os
import logging

logger = logging.getLogger(__name__)

# Lazy-loaded pipeline
_diarization_pipeline = None


def _get_pipeline():
    global _diarization_pipeline
    if _diarization_pipeline is None:
        try:
            from pyannote.audio import Pipeline
            hf_token = os.environ.get("HF_TOKEN")
            if not hf_token:
                raise ValueError("HF_TOKEN environment variable is required for pyannote.audio")

            _diarization_pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=hf_token,
            )
            logger.info("Loaded pyannote speaker diarization pipeline")
        except Exception as e:
            logger.error(f"Failed to load diarization pipeline: {e}")
            raise
    return _diarization_pipeline


class SpeakerDiarizer:
    """
    Assigns a speaker label to each transcript segment.

    Model: pyannote/speaker-diarization-3.1
    Internals:
    - ECAPA-TDNN neural speaker embedding model
    - Spectral clustering on cosine similarity matrix of embeddings
    - Silhouette score used for optimal number of speakers
    """

    def __init__(self):
        pass

    def diarize(self, audio_path: str) -> list[dict]:
        """
        Returns list of speaker-time segments:
        [
            {"speaker": "SPEAKER_00", "start": 0.0, "end": 3.2},
            {"speaker": "SPEAKER_01", "start": 3.5, "end": 7.1},
        ]
        """
        pipeline = _get_pipeline()
        try:
            diarization = pipeline(audio_path)
            segments = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                segments.append({
                    "speaker": speaker,
                    "start": turn.start,
                    "end": turn.end,
                })
            logger.info(f"Diarized {audio_path}: {len(segments)} speaker segments")
            return segments
        except Exception as e:
            logger.error(f"Diarization failed for {audio_path}: {e}")
            raise

    def align(self, transcript_segments: list[dict], diarization_segments: list[dict]) -> list[dict]:
        """
        Merges Whisper output with diarization output by matching time ranges.

        Matching rule: assign transcript segment to whichever speaker label has the
        most overlap with that segment's time range.

        Returns:
        [
            {"speaker": "SPEAKER_00", "text": "Let's talk about the budget.", "start": 0.0, "end": 2.4},
        ]
        """
        aligned = []
        for t_seg in transcript_segments:
            t_start = t_seg["start"]
            t_end = t_seg["end"]
            best_speaker = "SPEAKER_UNKNOWN"
            best_overlap = 0.0

            for d_seg in diarization_segments:
                overlap_start = max(t_start, d_seg["start"])
                overlap_end = min(t_end, d_seg["end"])
                overlap = max(0.0, overlap_end - overlap_start)

                if overlap > best_overlap:
                    best_overlap = overlap
                    best_speaker = d_seg["speaker"]

            aligned.append({
                "speaker": best_speaker,
                "text": t_seg["text"],
                "start": t_start,
                "end": t_end,
                "confidence": t_seg.get("confidence", 0.0),
            })

        return aligned
