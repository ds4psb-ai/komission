import sys
import os

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.sheet_manager import SheetManager
from app.services.outlier_selector import OutlierSelector
import google.auth

def main():
    print("🚀 Running Outlier Selector Logic...")
    
    # Auth (using ADC or gcloud token logic similar to setup)
    # For simplicity in this run script, we rely on ADC if available, 
    # or the SheetManager will handle default auth.
    
    try:
        manager = SheetManager() # Will use default credentials
        selector = OutlierSelector(manager)
        
        selector.process_new_outliers()
        
        print("✅ Selector run complete. Check Sheets for updates.")
        
    except Exception as e:
        print(f"❌ Error running selector: {e}")

if __name__ == "__main__":
    main()
