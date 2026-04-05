"""
BERT NER-based Task Extractor.

Uses HuggingFace dslim/bert-base-NER (pre-trained, no fine-tuning needed).
Extracts PERSON (assignee), DATE/TIME (deadline), and action verbs from
sentences classified as action_item or deadline_mention.

ML Concept: Transfer Learning — BERT pre-trained on BookCorpus/Wikipedia,
fine-tuned on CoNLL-2003 NER dataset.
"""

import re
import logging

logger = logging.getLogger(__name__)

# Lazy-loaded pipeline (heavy import)
_ner_pipeline = None


def _get_pipeline():
    global _ner_pipeline
    if _ner_pipeline is None:
        try:
            from transformers import pipeline
            _ner_pipeline = pipeline(
                "ner",
                model="dslim/bert-base-NER",
                aggregation_strategy="simple",
                device=-1,  # CPU; set to 0 for GPU
            )
            logger.info("Loaded BERT NER pipeline (dslim/bert-base-NER)")
        except Exception as e:
            logger.error(f"Failed to load NER pipeline: {e}")
            raise
    return _ner_pipeline


# Common action verbs for task extraction
_ACTION_VERBS = {
    "send", "finish", "complete", "review", "prepare", "create",
    "update", "schedule", "book", "call", "email", "write",
    "draft", "submit", "check", "fix", "deploy", "test",
    "design", "implement", "research", "analyse", "analyze",
    "coordinate", "organise", "organize", "share", "follow",
    "set", "make", "do", "get", "give", "take", "start",
}


class TaskExtractor:
    """
    Extracts: PERSON (assignee), DATE/TIME (deadline), TASK_VERB (action verb)
    from sentences classified as action_item or deadline_mention.

    Model: dslim/bert-base-NER (HuggingFace)
    This uses transfer learning — BERT pre-trained on BookCorpus/Wikipedia,
    fine-tuned on CoNLL-2003 NER dataset. No additional training needed.
    """

    def __init__(self):
        # Pipeline is lazy-loaded on first use
        pass

    def extract(self, sentence: str, speaker_name: str = None) -> dict:
        """
        Extract task metadata from a sentence.

        Returns:
        {
            "assignee": "Priya",            # or None
            "assignee_email": None,          # filled in later by identity mapper
            "deadline": "Wednesday",          # or None
            "task_verb": "finish",            # or None
            "task_description": "...",        # full cleaned sentence
            "confidence": 0.91
        }

        Fallback logic (CRITICAL):
        1. If NER finds a PERSON entity → use as assignee
        2. Elif sentence starts with "I will / I'll / I can" → assignee = speaker_name
        3. Elif sentence contains "we should/we need to" → assignee = "Team"
        4. Else → assignee = None (unassigned)
        """
        result = {
            "assignee": None,
            "assignee_email": None,
            "deadline": None,
            "task_verb": None,
            "task_description": sentence.strip(),
            "confidence": 0.0,
        }

        try:
            ner = _get_pipeline()
            entities = ner(sentence)
        except Exception as e:
            logger.error(f"NER inference failed: {e}")
            # Still apply fallback rules
            entities = []

        # --- Extract PERSON entities ---
        persons = [
            ent for ent in entities
            if ent.get("entity_group") == "PER"
        ]
        if persons:
            # Use the highest-scoring person
            best_person = max(persons, key=lambda e: e.get("score", 0))
            result["assignee"] = best_person["word"].strip()
            result["confidence"] = best_person.get("score", 0.0)

        # --- Fallback assignee logic ---
        if result["assignee"] is None:
            s_lower = sentence.strip().lower()
            # Rule 2: self-assignment
            if re.match(r"^(i will|i'll|i can|i am going to|i'm going to|let me)", s_lower):
                result["assignee"] = speaker_name or "Speaker"
                result["confidence"] = 0.7
            # Rule 3: team assignment
            elif re.search(r"\b(we should|we need to|we have to|we must|we can|let's|let us)\b", s_lower):
                result["assignee"] = "Team"
                result["confidence"] = 0.6
            else:
                result["assignee"] = None
                result["confidence"] = 0.3

        # --- Extract DATE/TIME entities ---
        dates = [
            ent for ent in entities
            if ent.get("entity_group") in ("DATE", "TIME", "MISC")
        ]
        if dates:
            result["deadline"] = dates[0]["word"].strip()
        else:
            # Regex fallback for common deadline patterns
            deadline_match = re.search(
                r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday|'
                r'tomorrow|today|next week|end of day|eod|eow|end of week|'
                r'by \w+|before \w+|until \w+)\b',
                sentence, re.IGNORECASE
            )
            if deadline_match:
                result["deadline"] = deadline_match.group(0).strip()

        # --- Extract action verb ---
        tokens = re.findall(r'\b\w+\b', sentence.lower())
        for token in tokens:
            if token in _ACTION_VERBS:
                result["task_verb"] = token
                break

        return result
