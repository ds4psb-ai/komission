#!/bin/bash

# Navigate to the backend directory
cd "$(dirname "$0")/.."

# Activate virtual environment
source venv/bin/activate

# Load environment variables (if not automatically handled by python-dotenv)
# export $(cat .env | xargs)

# Run the pipeline script
echo "[$(date)] Starting Daily Evidence Loop..."
python scripts/run_real_evidence_loop.py

# Optional: Logging is already handled by the python script (to stderr/stdout)
# You can redirect this script's output to a log file in the crontab entry.
