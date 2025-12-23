import sys
import os
import asyncio

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.sheet_manager import SheetManager
from app.services.opal_engine import OpalEngine
import google.auth
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

async def main():
    print("💎 Running Opal Decision Engine...")
    
    # Auth
    token = get_gcloud_token()
    creds = None
    if token:
        print("✅ Acquired gcloud access token.")
        scopes = ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/spreadsheets"]
        creds = google.oauth2.credentials.Credentials(token, scopes=scopes)
    else:
        print("⚠️ Utilizing default credentials...")

    try:
        manager = SheetManager(credentials=creds)
        engine = OpalEngine(manager)
        
        await engine.run_cycle()
        
        print("✅ Opal Cycle Complete. Check VDG_Decision sheet.")
        
    except Exception as e:
        print(f"❌ Error running Opal: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
