"""
Opal Engine: Automated Decision Making for Evidence Loop
Reads Evidence -> Generates Decision -> Writes to Sheet
"""
import json
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from app.services.sheet_manager import SheetManager
from app.services.gemini_pipeline import gemini_pipeline
from app.config import settings

class OpalEngine:
    def __init__(self, sheet_manager: SheetManager):
        self.sheet_manager = sheet_manager
        # Use gemini_pipeline's client or create a new one if strictly needed
        # For decision making, we can use a simpler text model or the same one
        self.client = gemini_pipeline.client 
        self.model = "gemini-2.0-flash-exp" # Fast model for reasoning

    async def run_cycle(self):
        """
        Main execution loop:
        1. Fetch pending evidence from VDG_Evidence
        2. Group by Parent ID
        3. For each group, generate decision (Opal)
        4. Write to VDG_Decision
        """
        print("💎 Opal Engine: Starting Cycle...")
        
        # 1. Fetch Evidence
        # Note: In a real app, we would query logic. 
        # For XML/Sheet/MVP, we read all and filter in memory or mock.
        # Here we assume we process 'VDG_Evidence' rows.
        # Since SheetManager.read_sheet is not fully implemented for structured data returning,
        # we will mock the "read" part for this MVP step or implement a simple reader.
        # For now, let's assume we proceed with the SAMPLE DATA inserted earlier.
        
        # TODO: Implement SheetManager.read_data() properly. 
        # For now, we will use a hardcoded sample representing "read from sheet" 
        # to demonstrate the Opal Logic.
        
        mock_evidence_group = {
            "parent_id": "parent-123",
            "parent_title": "Glass Skin Challenge",
            "variants": [
                {
                    "variant_name": "Original Sound",
                    "views": 50000,
                    "engagement_rate": "5%",
                    "retention_rate": "40%",
                    "confidence_score": 0.85
                },
                {
                    "variant_name": "Remix V1",
                    "views": 12000,
                    "engagement_rate": "3%",
                    "retention_rate": "20%",
                    "confidence_score": 0.45
                }
            ]
        }
        
        print(f"   Injesting evidence for: {mock_evidence_group['parent_title']}")
        
        # 2. Generate Decision
        decision = await self._generate_decision(mock_evidence_group)
        
        if decision:
            # 3. Write to Sheet
            self._write_decision(decision)
            print(f"✅ Decision written for {decision['parent_id']}")

    async def _generate_decision(self, evidence_group: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Calls Gemini to act as 'Opal' and make a GO/STOP decision
        """
        if not self.client:
            print("⚠️ No AI Client available, skipping decision generation.")
            return None

        prompt = f"""
        You are Opal, the Chief Decision Officer of a viral content engine.
        Analyze the following evidence test results and make a strategic decision.

        ### Context
        Parent Content: {evidence_group['parent_title']} (ID: {evidence_group['parent_id']})
        
        ### Evidence Data
        {json.dumps(evidence_group['variants'], indent=2)}

        ### Goal
        Maximize ROAS and Viral Reach. 
        - If clear winner (Confidence > 0.8), PROCEED to Scale.
        - If unclear, ITERATE or DEBATE.
        - If all fail, KILL.

        ### Output Format (JSON)
        {{
            "decision": "GO" | "STOP" | "ITERATE",
            "winner_variant_name": "string",
            "rationale": "One sentence summary of why.",
            "risks": "Potential downsides.",
            "next_experiment": "What to do next."
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
            
            # Enrich with IDs
            result["parent_id"] = evidence_group["parent_id"]
            result["decision_id"] = str(uuid.uuid4())
            result["created_at"] = datetime.now().isoformat()
            
            return result
        except Exception as e:
            print(f"❌ Opal AI Judgment Failed: {e}")
            return None

    def _write_decision(self, decision: Dict[str, Any]):
        """
        Writes the decision to VDG_Decision sheet
        Row Schema:
        decision_id, parent_id, winner_variant_id, winner_variant_name, 
        top_reasons, risks, next_experiment, sample_size, tracking_days, 
        success_criteria, status, created_at
        """
        row = [
            decision["decision_id"],
            decision["parent_id"],
            "var-unknown", # Placeholder as we didn't track variant ID in mock
            decision.get("winner_variant_name", "None"),
            decision.get("rationale", ""),
            decision.get("risks", ""),
            decision.get("next_experiment", ""),
            0, # sample_size
            7, # tracking_days
            "Auto-Generated",
            decision.get("decision", "DRAFT"),
            decision["created_at"]
        ]
        
        self.sheet_manager.append_data("VDG_Decision", [row])

