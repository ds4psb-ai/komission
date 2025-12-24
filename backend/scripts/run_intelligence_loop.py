"""
run_intelligence_loop.py
End-to-end LLM pipeline:
1. Generate Insights (NotebookLM-style analysis via Gemini)
2. Write to VDG_Insights sheet
3. Run Opal Decision Engine
4. Write to VDG_Decision sheet

Usage:
    python scripts/run_intelligence_loop.py [--parent-id PARENT_ID]
"""
import sys
import os
import asyncio
import json
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.sheet_manager import SheetManager
from app.services.opal_engine import OpalEngine
import google.auth
import google.oauth2.credentials
import subprocess


def get_gcloud_token():
    try:
        scopes = "https://www.googleapis.com/auth/drive,https://www.googleapis.com/auth/spreadsheets"
        result = subprocess.run(
            ['gcloud', 'auth', 'print-access-token', f'--scopes={scopes}'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except Exception as e:
        print(f"⚠️ Failed to get gcloud token: {e}")
        return None


class InsightsGenerator:
    """
    Generates NotebookLM-style insights using Gemini.
    Simulates the 'Idea Acquisition' phase.
    """
    def __init__(self, sheet_manager: SheetManager):
        self.sheet_manager = sheet_manager
        try:
            from app.services.gemini_pipeline import gemini_pipeline
            self.client = gemini_pipeline.client
            self.model = "gemini-2.0-flash-exp"
        except Exception as e:
            print(f"⚠️ Gemini client not available: {e}")
            self.client = None

    async def generate_insights(self, parent_id: str, parent_title: str, context: str) -> Optional[Dict[str, Any]]:
        """
        Generate insights from content context (simulating NotebookLM analysis)
        """
        if not self.client:
            print("⚠️ No AI Client available")
            return None

        prompt = f"""
        You are a senior content analyst for a viral short-form video platform.
        Analyze the following content and generate strategic insights.

        ### Content
        Parent ID: {parent_id}
        Title: {parent_title}
        Context: {context}

        ### Output Format (JSON)
        {{
            "summary": "2-3 sentence summary of the content's viral potential",
            "key_patterns": [
                "Pattern 1: Hook technique used",
                "Pattern 2: Visual trend detected",
                "Pattern 3: Audio strategy"
            ],
            "risks": [
                "Risk 1: Potential issue",
                "Risk 2: Content concern"
            ],
            "recommended_variants": [
                {{
                    "name": "Variant Name",
                    "hypothesis": "Why this would work",
                    "changes": ["Visual change", "Audio change", "Hook change"]
                }}
            ]
        }}
        """

        try:
            from google.genai import types
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            result = json.loads(response.text)
            result["parent_id"] = parent_id
            result["created_at"] = datetime.now().isoformat()
            return result
        except Exception as e:
            print(f"❌ Insights generation failed: {e}")
            return None

    def write_insights(self, insights: Dict[str, Any]):
        """
        Write insights to VDG_Insights sheet
        Schema: parent_id, summary, key_patterns, risks, created_at
        """
        row = [
            insights["parent_id"],
            insights.get("summary", ""),
            json.dumps(insights.get("key_patterns", []), ensure_ascii=False),
            json.dumps(insights.get("risks", []), ensure_ascii=False),
            insights["created_at"]
        ]
        self.sheet_manager.append_data("VDG_Insights", [row])
        print(f"✅ Insights written for {insights['parent_id']}")


async def run_full_loop(parent_id: Optional[str] = None):
    """
    Execute the complete intelligence loop:
    1. Generate Insights → VDG_Insights
    2. Generate Decision → VDG_Decision
    """
    print("=" * 50)
    print("🧠 KOMISSION INTELLIGENCE LOOP")
    print("=" * 50)

    # Auth Setup
    token = get_gcloud_token()
    creds = None
    if token:
        print("✅ Acquired gcloud access token")
        scopes = ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/spreadsheets"]
        creds = google.oauth2.credentials.Credentials(token, scopes=scopes)
    else:
        print("⚠️ Using default credentials...")

    try:
        manager = SheetManager(credentials=creds)
        
        # 1. INSIGHTS PHASE
        print("\n📊 Phase 1: Generating Insights...")
        insights_gen = InsightsGenerator(manager)
        
        # Sample Parent (in production, this would come from VDG_Parent_Candidates)
        sample_parent = {
            "parent_id": parent_id or f"parent-{uuid.uuid4().hex[:8]}",
            "title": "Glass Skin Challenge 2024",
            "context": """
                A beauty trend featuring 5-step skincare routines.
                Original sound: Lo-fi K-pop remix.
                Hook: 'POV: You discover the secret' with dramatic reveal.
                Visual: Raw/handheld phone footage, natural lighting.
                Engagement: 2.5M views, 15% save rate.
            """
        }
        
        insights = await insights_gen.generate_insights(
            sample_parent["parent_id"],
            sample_parent["title"],
            sample_parent["context"]
        )
        
        if insights:
            insights_gen.write_insights(insights)
            print(f"   Summary: {insights.get('summary', 'N/A')[:100]}...")
        
        # 2. DECISION PHASE
        print("\n💎 Phase 2: Running Opal Decision Engine...")
        engine = OpalEngine(manager)
        await engine.run_cycle()
        
        print("\n" + "=" * 50)
        print("✅ INTELLIGENCE LOOP COMPLETE")
        print("   → Check VDG_Insights sheet for analysis")
        print("   → Check VDG_Decision sheet for decisions")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Error in Intelligence Loop: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run Komission Intelligence Loop")
    parser.add_argument("--parent-id", type=str, help="Parent ID to process")
    args = parser.parse_args()
    
    asyncio.run(run_full_loop(args.parent_id))
