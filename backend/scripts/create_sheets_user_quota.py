import os
import sys
import logging
from dotenv import load_dotenv

# 1. Unset Service Account Env Var (Force User Auth)
if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
    del os.environ['GOOGLE_APPLICATION_CREDENTIALS']

# Add backend to path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

load_dotenv(os.path.join(BASE_DIR, ".env"), override=True)

# 2. Setup Config
SHEETS_TO_CREATE = [
    "VDG_Outlier_Raw",
    "VDG_Parent_Candidates", 
    "VDG_Evidence", 
    "VDG_Decision", 
    "VDG_Progress",
    "VDG_O2O_Campaigns",
    "VDG_O2O_Applications",
    "VDG_Insights",
    "VDG_Experiment"
]

FOLDER_ID = os.getenv("KOMISSION_FOLDER_ID")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.services.sheet_manager import SheetManager

def main():
    logger.info("🚀 Starting User-Auth Sheet Creation (Bypassing SA Quota)...")
    if not FOLDER_ID:
        logger.error("KOMISSION_FOLDER_ID not set in backend/.env")
        return
    
    # Initialize Manager (will fallback to google.auth.default -> gcloud)
    try:
        manager = SheetManager()
        logger.info(f"Authenticated as Project: {manager.project_id}")
        
        # Diagnostic: Check who we are
        about = manager.drive_service.about().get(fields="user").execute()
        user_email = about['user']['emailAddress']
        logger.info(f"👉 Operating as User: {user_email}")
        
        # Diagnostic: Check Folder
        try:
            folder = manager.drive_service.files().get(
                fileId=FOLDER_ID, 
                fields="id, name",
                supportsAllDrives=True
            ).execute()
            logger.info(f"✅ Found Folder: '{folder.get('name')}' ({folder.get('id')})")
        except Exception as e:
            logger.error(f"❌ Cannot access contents of Folder {FOLDER_ID}. Reason: {e}")
            logger.error("Double check the Folder ID or that your user has access.")
            return

    except Exception as e:
        logger.error(f"Auth/Init Failed: {e}")
        return

    created_count = 0
    for title in SHEETS_TO_CREATE:
        # Check existence first?
        # SheetManager.find_sheet_id searches by name.
        # But we must ensure we search inside the FOLDER or globally?
        # find_sheet_id logic: name = 'title' ...
        # If I use User Auth, I see everything.
        # Let's trust find_sheet_id logic.
        
        # Override manager folder_id for strictness
        manager.folder_id = FOLDER_ID
        
        existing_id = manager.find_sheet_id(title)
        if existing_id:
            logger.info(f"✅ {title} already exists ({existing_id}). Skipping.")
            continue
            
        try:
            sheet_id = manager.create_sheet(title, folder_id=FOLDER_ID)
            logger.info(f"✨ Created {title} ({sheet_id})")
            created_count += 1
        except Exception as e:
            logger.error(f"❌ Failed to create {title}: {e}")

    logger.info(f"🎉 Done. Created {created_count} sheets.")

if __name__ == "__main__":
    main()
