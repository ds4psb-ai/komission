"""
Test VDP Gold Pipeline Integration
"""
import asyncio
import sys
import os
import json
import logging

logging.basicConfig(level=logging.INFO)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.gemini_pipeline import gemini_pipeline

async def main():
    print("🚀 Testing VDP Gold Pipeline...")
    print("="*70)
    
    url = "https://www.youtube.com/shorts/d_ScVrX_ulI"
    node_id = "test_vdp_gold"
    
    try:
        print(f"Analyzing: {url}")
        print()
        
        result = await gemini_pipeline.analyze_video(url, node_id)
        
        print("\n✅ VDP GOLD ANALYSIS SUCCESS!")
        print("="*70)
        
        # Overall
        print("\n📌 OVERALL ANALYSIS")
        print(f"  Summary: {result.overall_analysis.summary[:100]}...")
        print(f"  Emotional Arc: {result.overall_analysis.emotional_arc}")
        
        # Hook
        hook = result.overall_analysis.hook_genome
        print(f"\n🎣 HOOK GENOME")
        print(f"  Pattern: {hook.pattern}")
        print(f"  Delivery: {hook.delivery}")
        print(f"  Strength: {hook.strength}")
        
        # Scenes
        print(f"\n🎬 SCENES ({len(result.scenes)} total)")
        for scene in result.scenes[:3]:
            print(f"  [{scene.scene_id}] {scene.narrative_unit.role}")
            print(f"    Time: {scene.time_start}s - {scene.time_end}s")
            print(f"    Summary: {scene.narrative_unit.summary[:80]}...")
            print(f"    Shots: {len(scene.shots)}")
            for shot in scene.shots[:2]:
                print(f"      - {shot.shot_id}: {shot.camera.shot} / {shot.camera.move}")
                if shot.keyframes:
                    for kf in shot.keyframes[:2]:
                        print(f"        [{kf.role}] {kf.desc[:50]}...")
        
        # Intent
        print(f"\n🧠 INTENT LAYER")
        print(f"  Trigger: {result.intent_layer.hook_trigger}")
        print(f"  Reason: {result.intent_layer.hook_trigger_reason[:100]}...")
        print(f"  Retention: {result.intent_layer.retention_strategy[:100]}...")
        
        # Remix
        print(f"\n💡 REMIX SUGGESTIONS ({len(result.remix_suggestions)})")
        for remix in result.remix_suggestions[:3]:
            print(f"  [{remix.target_niche}]")
            print(f"    {remix.concept[:80]}...")
        
        # Capsule Brief
        print(f"\n🎯 CAPSULE BRIEF (Shooting Guide)")
        print(f"  Hook: {result.capsule_brief.hook}")
        print(f"  Shotlist: {len(result.capsule_brief.shotlist)} shots")
        for shot in result.capsule_brief.shotlist[:3]:
            print(f"    {shot.seq}. [{shot.shot}] {shot.action[:50]}... ({shot.duration}s)")
        
        # Legacy Check
        print(f"\n🔗 LEGACY COMPATIBILITY")
        print(f"  global_context exists: {result.global_context is not None}")
        if result.global_context:
            print(f"  hook_pattern: {result.global_context.get('hook_pattern')}")
            print(f"  hook_strength_score: {result.global_context.get('hook_strength_score')}")
        print(f"  scene_frames count: {len(result.scene_frames) if result.scene_frames else 0}")
        
        print("\n" + "="*70)
        print("✅ VDP GOLD TEST COMPLETE")
        
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
