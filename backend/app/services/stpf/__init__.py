"""
STPF (Single Truth Pattern Formalization) v3.1 Package

Computational Truth Engine for viral video analysis.

Components:
- schemas: Pydantic models (Gates, Numerator, Denominator, Multipliers, Result)
- invariant_rules: 12 immutable rules validator
- calculator: STPF score calculator
- vdg_mapper: VDG → STPF variable mapper
- service: Service layer for API integration
- bayesian_updater: Pattern confidence updater ✅ Week 2
- reality_patches: Outlier correction patches ✅ Week 2
- anchors: VDG Scale Anchors (1-10) ✅ Week 2
- simulator: ToT + Monte Carlo (Week 3)
- kelly_criterion: Go/No-Go decision engine (Week 3)
"""

from app.services.stpf.schemas import (
    STPFGates,
    STPFNumerator,
    STPFDenominator,
    STPFMultipliers,
    STPFResult,
)
from app.services.stpf.invariant_rules import STPFInvariantRules
from app.services.stpf.calculator import STPFCalculator, stpf_calculator
from app.services.stpf.vdg_mapper import VDGToSTPFMapper, vdg_to_stpf_mapper
from app.services.stpf.service import STPFService, stpf_service

# Week 2 modules
from app.services.stpf.bayesian_updater import (
    BayesianPatternUpdater,
    bayesian_updater,
    BayesianPrior,
    PatternEvidence,
    BayesianPosterior,
)
from app.services.stpf.reality_patches import (
    RealityDistortionPatches,
    reality_patches,
    PatchContext,
    PatchResult,
)
from app.services.stpf.anchors import (
    VDG_SCALE_ANCHORS,
    VDGAnchorLookup,
    anchor_lookup,
)

__all__ = [
    # Schemas
    "STPFGates",
    "STPFNumerator",
    "STPFDenominator",
    "STPFMultipliers",
    "STPFResult",
    # Core
    "STPFInvariantRules",
    "STPFCalculator",
    "stpf_calculator",
    # Mapper
    "VDGToSTPFMapper",
    "vdg_to_stpf_mapper",
    # Service
    "STPFService",
    "stpf_service",
    # Week 2: Bayesian
    "BayesianPatternUpdater",
    "bayesian_updater",
    "BayesianPrior",
    "PatternEvidence",
    "BayesianPosterior",
    # Week 2: Reality Patches
    "RealityDistortionPatches",
    "reality_patches",
    "PatchContext",
    "PatchResult",
    # Week 2: Anchors
    "VDG_SCALE_ANCHORS",
    "VDGAnchorLookup",
    "anchor_lookup",
]
