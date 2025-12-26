"""
Test VDG v3.0 Pipeline Integration
"""
import asyncio
import sys
import os
import logging

logging.basicConfig(level=logging.INFO)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.gemini_pipeline import gemini_pipeline

async def main():
    print("🚀 Testing VDG v3.0 Pipeline...")
    print("="*70)
    
    url = "https://www.youtube.com/shorts/d_ScVrX_ulI"
    node_id = "test_vdg_v3"
    
    try:
        print(f"Analyzing: {url}")
        print()
        
        result = await gemini_pipeline.analyze_video(url, node_id)
        
        print("\n✅ VDG ANALYSIS SUCCESS!")
        print("="*70)
        
        # Identity
        print(f"Title: {result.title}")
        print(f"Summary: {result.summary}")
        
        # Hook & Psychology
        print(f"\n🧠 BRAIN (Psychology)")
        print(f"  Hook: {result.hook_genome.hook_summary} ({result.hook_genome.strength})")
        print(f"  Trigger: {result.intent_layer.hook_trigger}")
        
        irony = result.intent_layer.irony_analysis
        print(f"  Irony Gap ({irony.gap_type}):")
        print(f"    - Setup: {irony.setup}")
        print(f"    - Twist: {irony.twist}")
        
        radar = result.intent_layer.dopamine_radar
        print(f"  Dopamine Radar:")
        print(f"    - Visual: {radar.visual_spectacle}")
        print(f"    - Audio: {radar.audio_stimulation}")
        print(f"    - Comedy: {radar.comedy_shock}")
        
        # Meat (Structure)
        print(f"\n🥩 MEAT (Structure) - {len(result.scenes)} Scenes")
        for s in result.scenes:
            print(f"  [{s.narrative_unit.role}] {s.narrative_unit.summary[:60]}... ({len(s.shots)} shots)")
        
        # Hands (Action)
        print(f"\n👐 HANDS (Action Guide)")
        const = result.capsule_brief.constraints
        print(f"  Difficulty: {const.difficulty}")
        print(f"  Challenge: {const.primary_challenge}")
        print(f"  Props: {const.props}")
        
        print("\n" + "="*70)
        
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
