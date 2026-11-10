"""
Unit tests for QueryIntentClassifier.

Verifies:
    1. Pure aggregate / structural queries map to SCHEMA_ONLY.
    2. Direct entity lookups map to ENTITY_ONLY.
    3. Combined entity + analytical queries map to HYBRID_BOTH.
"""
import pytest

from enterprise_ai_platform.text_to_sql.intent_classifier import (
    QueryIntentClassifier,
)
from enterprise_ai_platform.text_to_sql import RetrievalIntent


class TestQueryIntentClassifier:
    """Tests for intent routing heuristic classifier."""

    def test_schema_only_analytical_queries(self) -> None:
        """Aggregate/structural queries without entity names resolve to SCHEMA_ONLY."""
        classifier = QueryIntentClassifier()

        assert classifier.classify_intent("How many employees are in each vertical?") == RetrievalIntent.SCHEMA_ONLY
        assert classifier.classify_intent("Show total count of active projects grouped by status") == RetrievalIntent.SCHEMA_ONLY
        assert classifier.classify_intent("What is the average attendance hours per department?") == RetrievalIntent.SCHEMA_ONLY
        assert classifier.classify_intent("List all tables related to appraisals") == RetrievalIntent.SCHEMA_ONLY

    def test_entity_only_direct_lookup_queries(self) -> None:
        """Direct lookup queries resolve to ENTITY_ONLY."""
        classifier = QueryIntentClassifier()

        assert classifier.classify_intent("Who is John Doe?") == RetrievalIntent.ENTITY_ONLY
        assert classifier.classify_intent("What is the email of John Doe?") == RetrievalIntent.ENTITY_ONLY
        assert classifier.classify_intent("Contact for PRJ-001") == RetrievalIntent.ENTITY_ONLY

    def test_hybrid_both_entity_and_analytical_queries(self) -> None:
        """Queries combining specific entity names with analytics resolve to HYBRID_BOTH."""
        classifier = QueryIntentClassifier()

        # Mentioning specific project name 'Apollo'
        assert classifier.classify_intent("What is the milestone progress for the Apollo project?") == RetrievalIntent.HYBRID_BOTH
        # Mentioning specific code 'CHAIO'
        assert classifier.classify_intent("Show total headcount in CHAIO") == RetrievalIntent.HYBRID_BOTH
        # Quoted entity
        assert classifier.classify_intent("Find all tasks assigned to 'Sarah Connor'") == RetrievalIntent.HYBRID_BOTH
