"""
Debate Engine: AI vs AI Debate for High Stakes Decisions
Optimist vs Skeptic -> Transcript -> Final Verdict
"""
import json
import uuid
from typing import Optional, Dict, Any
from app.services.sheet_manager import SheetManager
from app.services.gemini_pipeline import gemini_pipeline
from app.utils.time import utcnow

class DebateEngine:
    def __init__(self, sheet_manager: SheetManager):
        self.sheet_manager = sheet_manager
        self.client = gemini_pipeline.client 
        self.model = "gemini-3.0-pro"

    async def run_debate_cycle(self):
        """
        Main execution loop:
        1. Find "Controversial" Parents (e.g. high metrics but high risk, or internal conflict)
        2. Trigger Debate
        3. Save Transcript to Evidence/Decision Sheet (or dedicated log)
        """
        print("⚔️ Debate Engine: Looking for conflicts...")
        
        # Mocking a controversial case
        mock_case = {
            "parent_id": "case-999",
            "title": "Deepfake Celeb Parody",
            "category": "Comedy",
            "metrics": {"views": "1M+", "risk_score": "High"},
            "variants": [
                {"name": "Direct Parody", "performance": "High"},
                {"name": "Safe Version", "performance": "Low"}
            ]
        }
        
        print(f"   Debating: {mock_case['title']}")
        
        # 1. Generate Transcript
        transcript = await self._generate_transcript(mock_case)
        
        if transcript:
            # 2. Write Result (As a Decision with 'debate' status or similar)
            self._write_debate_result(transcript, mock_case)
            print(f"✅ Debate concluded for {mock_case['title']}")

    async def _generate_transcript(self, case_data: Dict[str, Any]) -> Optional[str]:
        if not self.client:
            return None

        prompt = f"""
        Simulate a debate between two AI personas about a viral content strategy.
        
        Case: {json.dumps(case_data)}
        
        Persona A (The Optimist):
        - Focuses on growth, viral potential, and "breaking the rules" for attention.
        - Metrics driven (Views, CTR).
        
        Persona B (The Skeptic):
        - Focuses on brand safety, legal risks, and long-term sustainability.
        - Worries about platform bans and copyright.
        
        Format:
        Round 1: Optimist proposes, Skeptic counters.
        Round 2: Optimist rebuts, Skeptic final warning.
        Conclusion: Joint agreement on GO or STOP.
        
        Output: A full dialogue transcript followed by "VERDICT: [GO|STOP]".
        """

        try:
            from google.genai import types
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            return response.text
        except Exception as e:
            print(f"❌ Debate Failed: {e}")
            return None

    def _write_debate_result(self, transcript: str, case_data: Dict[str, Any]):
        """
        Writes to VDG_Decision as a special entry
        """
        # Determine Verdict from text
        verdict = "STOP"
        if "VERDICT: GO" in transcript:
            verdict = "GO"
        elif "VERDICT: STOP" in transcript:
            verdict = "STOP"
            
        row = [
            str(uuid.uuid4()),
            case_data["parent_id"],
            "debate-result", 
            "Debate Conclusion",
            f"Debate Transcript Summary: {transcript[:200]}...", # Truncated for sheet efficiency
            "High Risk flag triggers debate", # Risk
            "Proceed with caution" if verdict == "GO" else "Kill project",
            0,
            0,
            "Debate Consensus",
            "debate_" + verdict.lower(),
            utcnow().isoformat()
        ]
        
        self.sheet_manager.append_data("VDG_Decision", [row])
