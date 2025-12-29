import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../"))

try:
    print("Checking imports...")
    from app.services.vdg_2pass.semantic_pass import SemanticPass
    from app.services.vdg_2pass.visual_pass import VisualPass
    from app.services.vdg_2pass.analysis_planner import AnalysisPlanner
    from app.services.vdg_2pass.merger import VDGMerger
    from app.services.vdg_2pass.director_compiler import DirectorCompiler
    from app.services.gemini_pipeline import GeminiPipeline
    
    print("✅ All modules imported successfully.")
    
    # Check instantiation
    p = GeminiPipeline()
    if hasattr(p, 'analyze_video_v4'):
        print("✅ analyze_video_v4 method exists.")
    else:
        print("❌ analyze_video_v4 method MISSING.")
        exit(1)
        
except Exception as e:
    print(f"❌ Import failed: {e}")
    exit(1)
