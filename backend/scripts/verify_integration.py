import asyncio
import sys
import os
import logging

# Setup Logger
logging.basicConfig(level=logging.INFO)

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.gemini_pipeline import gemini_pipeline

async def main():
    print("🚀 Testing Pipeline Integration...")
    
    # Real video that worked before
    url = "https://www.youtube.com/shorts/d_ScVrX_ulI"
    node_id = "test_node_integration"
    
    try:
        print(f"Analyzing {url}...")
        result = await gemini_pipeline.analyze_video(url, node_id)
        
        print("\n✅ VDG Analysis Success!")
        print("="*60)
        print("VDG Schema Check:")
        print(f"  - Platform: {result.meta_info.platform}")
        print(f"  - Duration: {result.meta_info.duration}s")
        print(f"  - Hook Summary: {result.hook_genome.hook_summary}")
        print(f"  - Intent Trigger: {result.intent_analysis.hook_trigger}")
        
        print("\nRemix Ideas:")
        for idea in result.remix_potentials:
            print(f"  * [{idea.target_niche}] {idea.concept}")
            
        print("\nLegacy Adapter Check:")
        if result.global_context:
            print(f"  - global_context exists: {result.global_context is not None}")
            print(f"  - hook_pattern: {result.global_context.get('hook_pattern')}")
            print(f"  - hook_strength_score: {result.global_context.get('hook_strength_score')}")
            print(f"  - keywords: {result.global_context.get('keywords')}")
        else:
            print("  ❌ global_context MISSING!")

        if result.scene_frames:
             print(f"  - scene_frames count: {len(result.scene_frames)}")
        else:
             print("  ❌ scene_frames MISSING!")
             
        print("="*60)

    except Exception as e:
        print(f"\n❌ Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
