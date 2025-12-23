import sys
import os
import asyncio

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.sheet_manager import SheetManager
from app.services.debate_engine import DebateEngine
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
        print(f"Failed to get gcloud token: {e}")
        return None

async def main():
    print("⚔️ Running Debate Engine...")
    
    token = get_gcloud_token()
    creds = None
    if token:
        scopes = ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/spreadsheets"]
        creds = google.oauth2.credentials.Credentials(token, scopes=scopes)

    try:
        manager = SheetManager(credentials=creds)
        engine = DebateEngine(manager)
        
        await engine.run_debate_cycle()
        
        print("✅ Debate Cycle Complete.")
        
    except Exception as e:
        print(f"❌ Error running Debate: {e}")

if __name__ == "__main__":
    asyncio.run(main())
