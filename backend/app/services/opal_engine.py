"""
Opal Engine: Automated Decision Making for Evidence Loop
Reads Evidence -> Generates Decision -> Writes to Sheet
"""
import json
import logging
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from app.services.sheet_manager import SheetManager
from app.services.gemini_pipeline import gemini_pipeline

logger = logging.getLogger(__name__)

class OpalEngine:
    def __init__(self, sheet_manager: SheetManager):
        self.sheet_manager = sheet_manager
        # Use gemini_pipeline's client
        self.client = gemini_pipeline.client
        self.model = "gemini-3.0-pro"
        
        # Fail-fast check for missing AI client
        if not self.client:
            logger.error("Gemini client not initialized. Check GOOGLE_API_KEY env var.")

    async def generate_and_save_decision(self, evidence_group: Dict[str, Any]):
        """
        Public method to trigger decision logic for a specific evidence group.
        Used by run_real_evidence_loop.py
        """
        if not self.client:
            raise RuntimeError("Gemini client not initialized. Check GOOGLE_API_KEY env var.")
        
        # Generate Decision
        decision = await self._generate_decision(evidence_group)
        
        if decision:
            # Write to Sheet
            self._write_decision(decision)
            logger.info(f"Decision written for parent_id={decision['parent_id']}")
        else:
            raise RuntimeError("Opal decision generation failed; no output to write.")

    async def _generate_decision(self, evidence_group: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Calls Gemini to act as 'Opal' and make a GO/STOP decision
        """
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
        except json.JSONDecodeError as e:
            logger.error(f"Opal AI returned invalid JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Opal AI Judgment Failed: {e}")
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
            "var-unknown",  # Placeholder as we didn't track variant ID
            decision.get("winner_variant_name", "None"),
            decision.get("rationale", ""),
            decision.get("risks", ""),
            decision.get("next_experiment", ""),
            0,  # sample_size
            7,  # tracking_days
            "Auto-Generated",
            decision.get("decision", "DRAFT"),
            decision["created_at"]
        ]
        
        self.sheet_manager.append_data("VDG_Decision", [row])
