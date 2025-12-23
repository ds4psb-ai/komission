import sys
import os
import asyncio
from pprint import pprint

# Add backend directory to sys.path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.services.gemini_pipeline import GeminiPipeline
from app.schemas.analysis import GeminiAnalysisResult

def test_mock_data_schema():
    print("🧪 Testing GeminiAnalysisResult Schema Compatibility...")
    
    pipeline = GeminiPipeline()
    try:
        # Test 1: Get Mock Data
        result = pipeline._get_mock_data("test-video-123")
        
        # Test 2: Verify Type
        assert isinstance(result, GeminiAnalysisResult), "Result is not of type GeminiAnalysisResult"
        
        # Test 3: Verify New Fields
        assert hasattr(result, 'timeline'), "Missing 'timeline' field"
        assert len(result.timeline) > 0, "Timeline is empty"
        assert hasattr(result, 'viral_hooks'), "Missing 'viral_hooks' field"
        assert result.virality_score > 0, "Virality score invalid"
        
        print("\n✅ Schema Verification PASSED!")
        print("-" * 30)
        print(f"Timeline Segments: {len(result.timeline)}")
        print(f"Viral Hooks: {len(result.viral_hooks)}")
        print(f"Virality Score: {result.virality_score}")
        print("-" * 30)
        
        # Print sample for manual check
        pprint(result.model_dump(exclude={'video_id'}))
        
    except Exception as e:
        print(f"\n❌ Schema Verification FAILED: {e}")
        # Print validation errors if any
        raise e

if __name__ == "__main__":
    test_mock_data_schema()
