"""
STPF (Single Truth Pattern Formalization) v3.1 Package

Computational Truth Engine for viral video analysis.

Components:
- schemas: Pydantic models (Gates, Numerator, Denominator, Multipliers, Result)
- invariant_rules: 12 immutable rules validator
- calculator: STPF score calculator
- bayesian_updater: Pattern confidence updater (Week 2)
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
from app.services.stpf.calculator import STPFCalculator

__all__ = [
    "STPFGates",
    "STPFNumerator",
    "STPFDenominator",
    "STPFMultipliers",
    "STPFResult",
    "STPFInvariantRules",
    "STPFCalculator",
]
