"""
Application Constants
backend/app/constants.py

Centralized constants to avoid magic numbers and ensure consistency.
"""

# ==================
# CONFIDENCE THRESHOLDS
# ==================
CONFIDENCE_HIGH = 0.8      # Ready for production/promotion
CONFIDENCE_MEDIUM = 0.7    # Ready for decision/review
CONFIDENCE_LOW = 0.6       # Minimum for Depth2 eligibility
CONFIDENCE_BASELINE = 0.5  # Random/no data

# ==================
# EXPERIMENT DURATIONS (days)
# ==================
EXPERIMENT_MIN_DAYS = 14           # Minimum tracking period
EXPERIMENT_FIRST_REVIEW_DAYS = 7   # First analysis checkpoint
EXPERIMENT_MAX_DAYS = 90           # Maximum tracking before forced decision

# ==================
# DEPTH2 SETTINGS
# ==================
DEPTH2_VARIANTS_COUNT = 3          # Number of refined variants to create
DEPTH2_TRACKING_DAYS = 14          # Depth2 experiment duration

# ==================
# RL-LITE SETTINGS
# ==================
RL_MIN_SIGNAL_COUNT = 5            # Minimum customizations to trigger update
RL_BATCH_UPDATE_INTERVAL_DAYS = 7  # Weekly batch updates

# ==================
# CUSTOMIZATION STORE
# ==================
CUSTOMIZATION_STORE_MAX_SIZE = 5000  # In-memory store limit

# ==================
# PATTERN ANALYSIS
# ==================
PATTERN_MIN_SAMPLES = 3            # Minimum samples for pattern lift calculation
PATTERN_LIFT_LIMIT = 20            # Default limit for pattern lifts query

# ==================
# OUTLIER DETECTION
# ==================
OUTLIER_TIER_S_MULTIPLIER = 10.0   # Views 10x+ creator average
OUTLIER_TIER_A_MULTIPLIER = 5.0    # Views 5x+ creator average
OUTLIER_TIER_B_MULTIPLIER = 3.0    # Views 3x+ creator average
