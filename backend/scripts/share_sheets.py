import sys
import os
import logging

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.sheet_manager import SheetManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    target_email = "ted.taeeun.kim@gmail.com"
    print(f"🚀 Sharing Evidence Loop Sheets with {target_email}...")
    
    try:
        manager = SheetManager()
        
        sheet_names = [
            "VDG_Outlier_Raw",
            "VDG_Parent_Candidates",
            "VDG_Evidence",
            "VDG_Decision",
            "VDG_Experiment",
            "VDG_Progress",
            "VDG_O2O_Campaigns",
            "VDG_O2O_Applications",
            "VDG_Insights"
        ]
        
        for name in sheet_names:
            sheet_id = manager.find_sheet_id(name)
            if sheet_id:
                manager.share_sheet(sheet_id, target_email)
                print(f"✅ Shared {name}")
            else:
                print(f"⚠️ Could not find {name}")
                
        print("\n🎉 Sharing Complete!")
        
    except Exception as e:
        print(f"❌ Error during sharing: {e}")

if __name__ == "__main__":
    main()
