import sys
import os
import random
import uuid
from datetime import datetime, timedelta

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.sheet_manager import SheetManager
import google.oauth2.credentials
import subprocess

def get_gcloud_token():
    try:
        # Requesting specific scopes for Drive and Spreadsheets
        scopes = "https://www.googleapis.com/auth/drive,https://www.googleapis.com/auth/spreadsheets"
        result = subprocess.run(
            ['gcloud', 'auth', 'print-access-token', f'--scopes={scopes}'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except Exception as e:
        print(f"Failed to get gcloud token: {e}")
        return None

def main():
    print("🚀 Populating Evidence Loop Sheets with Sample Data...")
    
    token = get_gcloud_token()
    creds = None
    if token:
        print("✅ Acquired gcloud access token.")
        scopes = ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/spreadsheets"]
        creds = google.oauth2.credentials.Credentials(token, scopes=scopes)
    else:
        print("⚠️ Could not get gcloud token, utilizing default credentials chain...")

    manager = SheetManager(credentials=creds)

    # 1. VDG_Outlier_Raw
    # | source_name | source_url | collected_at | platform | category | title | views | growth_rate | author | posted_at | status |
    outlier_rows = [
        ["TrendHunter", "https://example.com/trend1", datetime.now().isoformat(), "tiktok", "beauty", "Glass Skin Tutorial", 1500000, 1.5, "@glowskin", (datetime.now() - timedelta(days=2)).isoformat(), "candidate"],
        ["ViralFinds", "https://example.com/trend2", datetime.now().isoformat(), "instagram", "fashion", "Oversized Blazer", 800000, 1.2, "@fashionista", (datetime.now() - timedelta(days=5)).isoformat(), "new"],
    ]
    manager.append_data("VDG_Outlier_Raw", outlier_rows)
    print("✅ Populated VDG_Outlier_Raw")

    # 2. VDG_Parent_Candidates
    # | parent_id | title | platform | category | source_url | baseline_views | baseline_engagement | selected_by | selected_at | status |
    parent_id = str(uuid.uuid4())
    parent_rows = [
        [parent_id, "Glass Skin Challenge", "tiktok", "beauty", "https://example.com/trend1", 1500000, 0.15, "Agent", datetime.now().isoformat(), "depth1"]
    ]
    manager.append_data("VDG_Parent_Candidates", parent_rows)
    print("✅ Populated VDG_Parent_Candidates")

    # 3. VDG_Evidence
    # | evidence_id | parent_id | parent_title | depth | variant_id | variant_name | views | engagement_rate | retention_rate | tracking_days | confidence_score | confidence_ci_low | confidence_ci_high | rank | winner | generated_at |
    evidence_rows = [
        [str(uuid.uuid4()), parent_id, "Glass Skin Challenge", 1, str(uuid.uuid4()), "Original Sound", 50000, 0.05, 0.4, 7, 0.85, 0.8, 0.9, 1, True, datetime.now().isoformat()],
        [str(uuid.uuid4()), parent_id, "Glass Skin Challenge", 1, str(uuid.uuid4()), "Remix V1", 12000, 0.03, 0.2, 7, 0.45, 0.3, 0.5, 2, False, datetime.now().isoformat()]
    ]
    manager.append_data("VDG_Evidence", evidence_rows)
    print("✅ Populated VDG_Evidence")

    # 4. VDG_Decision (Mock)
    # | decision_id | parent_id | winner_variant_id | winner_variant_name | top_reasons | risks | next_experiment | sample_size | tracking_days | success_criteria | status | created_at |
    decision_rows = [
        [str(uuid.uuid4()), parent_id, "v-123", "Original Sound", "High retention, strong shares", "Music copyright", "Scale ad spend", 1000, 7, "ROAS > 2.0", "approved", datetime.now().isoformat()]
    ]
    manager.append_data("VDG_Decision", decision_rows)
    print("✅ Populated VDG_Decision")

    print("\n🎉 Sample Data Insertion Complete!")

if __name__ == "__main__":
    main()
