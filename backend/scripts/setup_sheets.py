import sys
import os

# Add backend directory to path so we can import app modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.sheet_manager import SheetManager
import subprocess
import google.oauth2.credentials

def get_gcloud_token():
    try:
        # Run gcloud command to get access token (cloud-platform scope covers Drive/Sheets)
        scopes = "https://www.googleapis.com/auth/cloud-platform"
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
    print("🚀 Evidence Loop Google Sheets Setup Starting...")
    
    try:
        token = get_gcloud_token()
        creds = None
        if token:
            print("✅ Acquired gcloud access token.")
            # Create credentials object with the token and scopes
            # Passing scopes here helps the library know what scopes are active
            # Use cloud-platform scope as that is what gcloud provided
            scopes = ["https://www.googleapis.com/auth/cloud-platform"]
            creds = google.oauth2.credentials.Credentials(token, scopes=scopes)
        else:
            print("⚠️ Could not get gcloud token, trying default credentials chain...")

        manager = SheetManager(credentials=creds)
        
        # Folder ID should be passed as an argument or env var if strictly required, 
        # but for now we'll create in root if not provided.
        # If user wants a specific folder, they should duplicate the script or we ask for input.
        # Here we assume root for simplicity as per "proceed automatically".
        
        created = manager.setup_evidence_loop()
        
        print("\n✅ Successfully created ALL sheets:")
        for title, sheet_id in created.items():
            print(f" - {title}: {sheet_id}")
            
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
