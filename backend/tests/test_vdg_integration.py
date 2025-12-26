"""
VDG Integration Tests
backend/tests/test_vdg_integration.py

Tests the full VDG analysis pipeline:
1. Schema normalization
2. Cluster assignment
3. NotebookLibraryEntry creation
4. Evidence snapshot generation
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import uuid
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestVDGPipelineIntegration:
    """Test the full VDG analysis → cluster → library pipeline"""
    
    @pytest.fixture
    def mock_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def sample_vdg_schema(self):
        """Sample VDG v3.2 schema from Gemini analysis"""
        return {
            "title": "Test Viral Video",
            "summary": "A viral short-form video with engaging hook",
            "hook_genome": {
                "pattern": "problem_solution",
                "delivery": "text_punch",
                "start_sec": 0.0,
                "end_sec": 2.5,
                "strength": 9,
                "microbeats": [
                    {"role": "setup", "cue": "text", "start": 0.0, "end": 0.8},
                    {"role": "build", "cue": "visual", "start": 0.8, "end": 1.5},
                    {"role": "punch", "cue": "audio", "start": 1.5, "end": 2.5},
                ]
            },
            "scenes": [
                {
                    "title": "Hook Scene",
                    "shots": [
                        {"camera": {"move": "zoom_in", "angle": "close_up"}, "start": 0, "end": 1.5},
                        {"camera": {"move": "pan", "angle": "medium"}, "start": 1.5, "end": 3.0},
                    ]
                }
            ],
            "intent_layer": {
                "hook_trigger": "curiosity",
                "content_category": "beauty",
                "target_audience": "gen_z"
            },
            "production_constraints": {
                "min_equipment": ["smartphone", "ring_light"],
                "skill_level": "beginner"
            }
        }
    
    def test_schema_normalization_vdg(self, mock_db, sample_vdg_schema):
        """VDG v3.2 schema normalizes correctly"""
        from app.services.clustering import PatternClusteringService
        
        service = PatternClusteringService(mock_db)
        normalized = service._normalize_schema(sample_vdg_schema)
        
        assert normalized["hook"]["type"] == "problem_solution"
        assert normalized["hook"]["duration_sec"] == 2.5
        assert len(normalized["microbeat_sequence"]) == 3
        assert "setup:text" in normalized["microbeat_sequence"]
        assert "zoom_in" in normalized["visual_patterns"]
    
    def test_cluster_id_from_hook_pattern(self, mock_db, sample_vdg_schema):
        """Cluster ID can be derived from hook pattern"""
        from app.services.clustering import PatternClusteringService
        
        service = PatternClusteringService(mock_db)
        normalized = service._normalize_schema(sample_vdg_schema)
        
        # Cluster ID would be based on hook pattern + visual patterns
        hook_type = normalized["hook"]["type"]
        assert hook_type == "problem_solution"
        # The actual cluster_id is generated in get_or_create_cluster (async)
    
    def test_similarity_calculation(self, mock_db, sample_vdg_schema):
        """Two identical schemas have high similarity"""
        from app.services.clustering import PatternClusteringService
        
        service = PatternClusteringService(mock_db)
        score = service.calculate_similarity(sample_vdg_schema, sample_vdg_schema)
        
        assert score >= 0.9
    
    def test_similar_but_different_schemas(self, mock_db, sample_vdg_schema):
        """Similar schemas with different hooks have moderate similarity"""
        from app.services.clustering import PatternClusteringService
        
        service = PatternClusteringService(mock_db)
        
        schema_b = sample_vdg_schema.copy()
        schema_b["hook_genome"] = {
            "pattern": "question",  # Different hook type
            "delivery": "text_punch",
            "start_sec": 0.0,
            "end_sec": 2.0,
            "microbeats": [
                {"role": "setup", "cue": "text", "start": 0.0, "end": 1.0},
                {"role": "punch", "cue": "visual", "start": 1.0, "end": 2.0},
            ]
        }
        
        score = service.calculate_similarity(sample_vdg_schema, schema_b)
        
        # Should be lower than identical but still related
        assert 0.3 <= score <= 0.8


class TestNotebookLibraryIntegration:
    """Test NotebookLibraryEntry creation from VDG analysis"""
    
    @pytest.fixture
    def sample_vdg_result(self):
        """Sample VDG analysis result object"""
        class MockVDGResult:
            title = "Test Video"
            summary = "Test summary"
            hook_genome = MagicMock()
            hook_genome.pattern = "problem_solution"
            
            def model_dump(self):
                return {
                    "title": self.title,
                    "summary": self.summary,
                    "hook_genome": {"pattern": "problem_solution"}
                }
        return MockVDGResult()
    
    def test_library_entry_fields(self, sample_vdg_result):
        """NotebookLibraryEntry has all required fields"""
        from app.models import NotebookLibraryEntry
        
        entry = NotebookLibraryEntry(
            source_url="https://tiktok.com/test",
            platform="tiktok",
            category="beauty",
            summary={
                "title": sample_vdg_result.title,
                "hook_pattern": sample_vdg_result.hook_genome.pattern,
            },
            cluster_id="test-cluster-1",
            analysis_schema=sample_vdg_result.model_dump(),
            schema_version="v3.2",
        )
        
        assert entry.source_url == "https://tiktok.com/test"
        assert entry.platform == "tiktok"
        assert entry.cluster_id == "test-cluster-1"
        assert entry.schema_version == "v3.2"
        assert entry.analysis_schema["title"] == "Test Video"


class TestEvidenceSnapshotIntegration:
    """Test Evidence snapshot creation from VDG data"""
    
    def test_evidence_snapshot_fields(self):
        """EvidenceSnapshot has all required fields"""
        from app.models import EvidenceSnapshot
        
        snapshot = EvidenceSnapshot(
            parent_node_id=uuid.uuid4(),
            snapshot_date=datetime.utcnow(),
            period="4w",
            depth1_summary={
                "audio": {"trending_beat": {"success_rate": 0.85, "sample_count": 12}},
                "visual": {"zoom_hook": {"success_rate": 0.72, "sample_count": 8}},
            },
            top_mutation_type="audio",
            top_mutation_pattern="trending_beat",
            top_mutation_rate="+127%",
            sample_count=20,
            confidence=0.85,
        )
        
        assert snapshot.period == "4w"
        assert snapshot.top_mutation_type == "audio"
        assert snapshot.sample_count == 20
        assert snapshot.confidence == 0.85


class TestMicrobeatsSequence:
    """Test microbeat sequence extraction and comparison"""
    
    @pytest.fixture
    def mock_db(self):
        return AsyncMock()
    
    def test_microbeat_extraction(self, mock_db):
        """Microbeats are correctly extracted from VDG schema"""
        from app.services.clustering import PatternClusteringService
        
        schema = {
            "hook_genome": {
                "microbeats": [
                    {"role": "setup", "cue": "text"},
                    {"role": "build", "cue": "visual"},
                    {"role": "punch", "cue": "audio"},
                ]
            }
        }
        
        service = PatternClusteringService(mock_db)
        normalized = service._normalize_schema(schema)
        
        assert normalized["microbeat_sequence"] == ["setup:text", "build:visual", "punch:audio"]
    
    def test_sequence_order_matters(self, mock_db):
        """Microbeat sequence order affects similarity"""
        from app.services.clustering import PatternClusteringService
        
        service = PatternClusteringService(mock_db)
        
        seq_a = ["setup:text", "build:visual", "punch:audio"]
        seq_b = ["punch:audio", "setup:text", "build:visual"]  # Reordered
        
        # Same elements but different order should have lower similarity
        score_same = service._sequence_similarity(seq_a, seq_a)
        score_reordered = service._sequence_similarity(seq_a, seq_b)
        
        assert score_same == 1.0
        assert score_reordered < score_same


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
