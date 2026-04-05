"""
BART Abstractive Meeting Summariser.

Model: sshleifer/distilbart-cnn-12-6 (lighter than bart-large-cnn, CPU-viable)

ML Concepts demonstrated:
- Seq2Seq: Encoder reads full input, decoder generates output token by token
- Beam Search: Keeps top-k candidate output sequences at each step
- Transfer Learning: Pre-trained on CNN/DailyMail dataset
"""

import logging

logger = logging.getLogger(__name__)

# Lazy-loaded pipeline
_summariser_pipeline = None


def _get_pipeline():
    global _summariser_pipeline
    if _summariser_pipeline is None:
        try:
            from transformers import pipeline, AutoModelForSeq2SeqLM, AutoTokenizer
            model_name = "sshleifer/distilbart-cnn-12-6"
            model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            _summariser_pipeline = pipeline(
                "summarization",
                model=model,
                tokenizer=tokenizer,
                device=-1,  # CPU
            )
            logger.info("Loaded BART summarisation pipeline (distilbart-cnn-12-6)")
        except Exception as e:
            logger.error(f"Failed to load summarisation pipeline: {e}")
            raise
    return _summariser_pipeline


class MeetingSummariser:
    """
    Generates a 3–5 sentence abstractive summary of the full meeting transcript.
    Model: sshleifer/distilbart-cnn-12-6 (lighter than bart-large-cnn, CPU-viable)

    Concept demonstrated: Seq2Seq, encoder-decoder attention, beam search decoding.
    """

    def __init__(self):
        pass

    def summarise(self, full_transcript: str) -> str:
        """
        full_transcript: concatenated string of all speaker-attributed sentences.
        e.g. "Priya: Let's start with the budget.\nRaj: The Q3 numbers look good..."

        If transcript > 900 tokens, chunk it with 100-token overlap and summarise
        each chunk, then summarise the chunk summaries (two-pass).

        Returns: 3–5 sentence summary string.
        """
        if not full_transcript or not full_transcript.strip():
            return "No transcript available to summarise."

        words = full_transcript.split()

        if len(words) <= 900:
            return self._summarise_chunk(full_transcript)

        # Two-pass chunked summarisation
        chunks = self._chunk_text(words, chunk_size=800, overlap=100)
        logger.info(f"Transcript has {len(words)} words, split into {len(chunks)} chunks")

        chunk_summaries = []
        for i, chunk in enumerate(chunks):
            summary = self._summarise_chunk(chunk)
            chunk_summaries.append(summary)
            logger.info(f"Chunk {i+1}/{len(chunks)} summarised")

        # Second pass: summarise the summaries
        combined = " ".join(chunk_summaries)
        return self._summarise_chunk(combined)

    def _summarise_chunk(self, text: str) -> str:
        """Summarise a single chunk of text."""
        try:
            pipe = _get_pipeline()
            result = pipe(
                text,
                max_length=150,
                min_length=40,
                do_sample=False,
                num_beams=4,
                length_penalty=2.0,
            )
            return result[0]["summary_text"]
        except Exception as e:
            logger.error(f"Summarisation failed: {e}")
            # Fallback: return first 3 sentences
            sentences = text.split(".")
            return ". ".join(sentences[:3]).strip() + "."

    @staticmethod
    def _chunk_text(words: list, chunk_size: int = 800, overlap: int = 100) -> list:
        """Split word list into overlapping chunks."""
        chunks = []
        start = 0
        while start < len(words):
            end = start + chunk_size
            chunk = " ".join(words[start:end])
            chunks.append(chunk)
            start += chunk_size - overlap
        return chunks
