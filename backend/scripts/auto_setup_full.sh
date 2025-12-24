#!/bin/bash
set -e

echo "🚀 Komission: Auto Setup & Pipeline Run"
echo "======================================="
echo "1. Authenticating User (for Drive Access)..."
echo "   (Please approve the login in your browser)"

# Force interactive login with Drive scopes
gcloud auth application-default login --scopes='https://www.googleapis.com/auth/drive','https://www.googleapis.com/auth/spreadsheets','https://www.googleapis.com/auth/cloud-platform'

echo "✅ Auth successful."

echo "2. Creating Sheets (User Quota)..."
python backend/scripts/create_sheets_user_quota.py

echo "3. Syncing Outliers..."
python backend/scripts/sync_outliers_to_sheet.py

echo "4. Running Real Evidence Loop..."
python backend/scripts/run_real_evidence_loop.py

echo "🎉 All Done!"
