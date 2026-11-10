"""
Query intent classification service.

Determines whether a natural language question requires SCHEMA_ONLY retrieval,
ENTITY_ONLY retrieval, or HYBRID_BOTH retrieval to optimize latency and token cost.
"""
import re

from enterprise_ai_platform.domain.structured_data.entity_document import (
    RetrievalIntent,
)

# Common indicators of analytical/aggregation queries
AGGREGATE_PATTERNS: tuple[str, ...] = (
    r"\bhow many\b",
    r"\btotal count\b",
    r"\baverage\b",
    r"\bavg\b",
    r"\bsum\b",
    r"\bmin\b",
    r"\bmax\b",
    r"\bgrouped by\b",
    r"\bper vertical\b",
    r"\bper department\b",
    r"\bdistribution\b",
    r"\boverall trend\b",
    r"\blist all tables\b",
    r"\ball columns\b",
)

# Entity value indicators (project codes, vertical codes, quotes, specific names)
ENTITY_PATTERNS: tuple[str, ...] = (
    r"\bprj-\d+\b",                      # PRJ-001, PRJ-102
    r"\bch(aio|dlo|tao|eno|hco|tfo)\b",  # CHAIO, CHDLO, CHTAO, etc.
    r"['\"][^'\"]+['\"]",                # Quoted strings: 'Apollo', "John"
    r"\bwho is\b",
    r"\bcontact for\b",
    r"\bemail of\b",
    r"\bdetails for project\b",
)


class QueryIntentClassifier:
    """
    Sub-millisecond heuristic query intent classifier for dynamic retrieval routing.
    """

    def classify_intent(self, query: str) -> RetrievalIntent:
        """
        Classify a natural language user query into a RetrievalIntent.

        Args:
            query: User's raw question string.

        Returns:
            RetrievalIntent (SCHEMA_ONLY, ENTITY_ONLY, or HYBRID_BOTH).
        """
        clean = query.strip()
        clean_lower = clean.lower()

        has_aggregate = any(
            re.search(pat, clean_lower) for pat in AGGREGATE_PATTERNS
        )
        has_entity = any(
            re.search(pat, clean_lower) for pat in ENTITY_PATTERNS
        )

        # Check for capitalized proper nouns/names (e.g. "Apollo", "John Doe")
        words = clean.split()
        capitalized_tokens = [
            w for w in words[1:]  # Skip the first word of sentence
            if w.istitle() and len(w) > 2 and w.lower() not in {"what", "which", "where", "show", "tell", "give"}
        ]
        if capitalized_tokens:
            has_entity = True

        # Routing decisions
        if has_aggregate and not has_entity:
            return RetrievalIntent.SCHEMA_ONLY

        if has_entity and not has_aggregate:
            # Check if it's purely a direct lookup
            if clean_lower.startswith(("who is", "what is the email", "find person", "contact for")):
                return RetrievalIntent.ENTITY_ONLY
            return RetrievalIntent.HYBRID_BOTH

        # Default to HYBRID_BOTH for mixed questions or general safety
        return RetrievalIntent.HYBRID_BOTH
