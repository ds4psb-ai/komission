"""
Tests for Pattern Clustering Service
backend/tests/test_clustering.py
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import uuid

# Import the service class
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.clustering import PatternClusteringService


class TestSequenceSimilarity:
    """Test microbeat sequence similarity calculation"""
    
    def setup_method(self):
        """Setup mock DB session"""
        self.mock_db = AsyncMock()
        self.service = PatternClusteringService(self.mock_db)
    
    def test_identical_sequences(self):
        """Identical sequences should return 1.0"""
        seq1 = ["start:visual", "build:audio", "punch:text"]
        seq2 = ["start:visual", "build:audio", "punch:text"]
        assert self.service._sequence_similarity(seq1, seq2) == 1.0
    
    def test_completely_different_sequences(self):
        """Completely different sequences should return low score"""
        seq1 = ["a", "b", "c"]
        seq2 = ["x", "y", "z"]
        score = self.service._sequence_similarity(seq1, seq2)
        assert score < 0.2  # High edit distance
    
    def test_one_edit_difference(self):
        """One element difference should still score high"""
        seq1 = ["start:visual", "build:audio", "punch:text"]
        seq2 = ["start:visual", "build:AUDIO", "punch:text"]  # One diff
        score = self.service._sequence_similarity(seq1, seq2)
        assert score > 0.6
    
    def test_empty_sequences(self):
        """Empty sequences should return default score"""
        assert self.service._sequence_similarity([], []) == 0.5
        assert self.service._sequence_similarity([], ["a"]) == 0.5
    
    def test_different_length_sequences(self):
        """Different length sequences should handle gracefully"""
        seq1 = ["a", "b", "c"]
        seq2 = ["a", "b", "c", "d", "e"]
        score = self.service._sequence_similarity(seq1, seq2)
        assert 0.0 <= score <= 1.0


class TestHookComparison:
    """Test hook comparison logic"""
    
    def setup_method(self):
        self.mock_db = AsyncMock()
        self.service = PatternClusteringService(self.mock_db)
    
    def test_same_hook_type_same_duration(self):
        """Same hook type with similar duration should score 1.0"""
        hook1 = {"type": "text_punch", "duration_sec": 2.0}
        hook2 = {"type": "text_punch", "duration_sec": 2.2}
        score = self.service._compare_hooks(hook1, hook2)
        assert score == 1.0
    
    def test_same_hook_type_different_duration(self):
        """Same hook type with different duration should score lower"""
        hook1 = {"type": "text_punch", "duration_sec": 2.0}
        hook2 = {"type": "text_punch", "duration_sec": 5.0}
        score = self.service._compare_hooks(hook1, hook2)
        assert score == 0.6  # duration_diff > 1.0
    
    def test_different_hook_types(self):
        """Different hook types should score low"""
        hook1 = {"type": "text_punch", "duration_sec": 2.0}
        hook2 = {"type": "zoom_in", "duration_sec": 2.0}
        score = self.service._compare_hooks(hook1, hook2)
        assert score == 0.3
    
    def test_missing_hooks(self):
        """Missing hooks should return None"""
        assert self.service._compare_hooks(None, {"type": "test"}) is None
        assert self.service._compare_hooks({}, {}) is None


class TestSchemaNoramlization:
    """Test schema normalization for VDG and legacy schemas"""
    
    def setup_method(self):
        self.mock_db = AsyncMock()
        self.service = PatternClusteringService(self.mock_db)
    
    def test_vdg_v3_schema_normalization(self):
        """VDG v3.x schema should be normalized correctly"""
        vdg_schema = {
            "hook_genome": {
                "pattern": "problem_solution",
                "delivery": "visual_gag",
                "start_sec": 0.0,
                "end_sec": 3.0,
                "microbeats": [
                    {"role": "start", "cue": "visual"},
                    {"role": "punch", "cue": "audio"}
                ]
            },
            "scenes": [
                {
                    "shots": [
                        {"camera": {"move": "zoom_in"}, "start": 0, "end": 1.5}
                    ]
                }
            ],
            "summary": "Test video"
        }
        
        normalized = self.service._normalize_schema(vdg_schema)
        
        assert normalized["hook"]["type"] == "problem_solution"
        assert normalized["hook"]["duration_sec"] == 3.0
        assert len(normalized["microbeat_sequence"]) == 2
        assert "start:visual" in normalized["microbeat_sequence"]
        assert "zoom_in" in normalized["visual_patterns"]
    
    def test_legacy_schema_normalization(self):
        """Legacy VideoAnalysisSchema should be normalized correctly"""
        legacy_schema = {
            "hook": {
                "attention_technique": "question",
                "hook_duration_sec": 2.5
            },
            "shots": [
                {"visual_pattern": "close_up", "audio_pattern": "music", "duration_sec": 1.0},
                {"visual_pattern": "wide", "audio_pattern": "sfx", "duration_sec": 2.0}
            ],
            "audio_is_trending": True,
            "primary_pattern": "question_hook"
        }
        
        normalized = self.service._normalize_schema(legacy_schema)
        
        assert normalized["hook"]["type"] == "question"
        assert normalized["hook"]["duration_sec"] == 2.5
        assert len(normalized["visual_patterns"]) == 2
        assert normalized["audio_flags"]["is_trending"] == True
    
    def test_legacy_schema_without_microbeats_fallback(self):
        """Legacy schema should generate pseudo-microbeats from shots"""
        legacy_schema = {
            "hook": {"attention_technique": "question"},
            "shots": [
                {"visual_pattern": "close_up", "audio_pattern": "music"},
                {"visual_pattern": "wide", "audio_pattern": "sfx"}
            ]
        }
        
        normalized = self.service._normalize_schema(legacy_schema)
        
        # Should have pseudo-microbeats from shots
        assert normalized["microbeat_sequence"] is not None
        assert len(normalized["microbeat_sequence"]) == 2
        assert "close_up:music" in normalized["microbeat_sequence"]


class TestCalculateSimilarity:
    """Test overall similarity calculation"""
    
    def setup_method(self):
        self.mock_db = AsyncMock()
        self.service = PatternClusteringService(self.mock_db)
    
    def test_identical_schemas(self):
        """Identical schemas should score very high"""
        schema = {
            "hook_genome": {
                "pattern": "problem_solution",
                "start_sec": 0, "end_sec": 3,
                "microbeats": [{"role": "start", "cue": "visual"}]
            },
            "scenes": [{"shots": [{"camera": {"move": "zoom"}, "start": 0, "end": 1}]}],
            "summary": "Test"
        }
        
        score = self.service.calculate_similarity(schema, schema)
        assert score >= 0.9
    
    def test_weight_distribution(self):
        """Weights should sum to 1.0"""
        total_weight = sum(self.service.WEIGHTS.values())
        assert abs(total_weight - 1.0) < 0.01


class TestPatternTypeInference:
    """Test pattern type inference from schema"""
    
    def setup_method(self):
        self.mock_db = AsyncMock()
        self.service = PatternClusteringService(self.mock_db)
    
    def test_semantic_pattern(self):
        """Text-based hooks should be classified as semantic"""
        schema = {"hook": {"attention_technique": "text_punch"}, "shots": []}
        assert self.service._infer_pattern_type(schema) == "semantic"
    
    def test_visual_pattern(self):
        """Visual hooks should be classified as visual"""
        schema = {"hook": {"attention_technique": "face_zoom"}, "shots": []}
        assert self.service._infer_pattern_type(schema) == "visual"
    
    def test_audio_pattern(self):
        """Trending audio should be classified as audio"""
        schema = {"hook": {"attention_technique": "other"}, "audio_is_trending": True, "shots": []}
        assert self.service._infer_pattern_type(schema) == "audio"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
