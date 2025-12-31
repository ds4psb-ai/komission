"""
Schema Validator (PEGL v1.0 Phase 0)

스키마 버전 검증 및 데이터 계약 강제

원칙:
- 모든 핵심 IO에 schema_version 필드 검증
- 스키마 불일치 시 **명시적 실패** (조용히 진행 금지)
- 지원되지 않는 버전은 거부

Usage:
    from app.validators.schema_validator import validate_schema_version, SchemaValidationError
    
    try:
        validate_schema_version(schema, context="gemini_analysis")
    except SchemaValidationError as e:
        log.error(f"Schema validation failed: {e}")
        raise
"""
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class SchemaValidationError(Exception):
    """스키마 검증 실패 예외"""
    
    def __init__(self, message: str, context: str = "", schema_version: Optional[str] = None):
        self.context = context
        self.schema_version = schema_version
        super().__init__(message)


# 지원되는 VDG 분석 스키마 버전
SUPPORTED_VDG_VERSIONS = ["v3.0", "v3.1", "v3.2", "v3.5", "v3.6"]

# 지원되는 Evidence 스키마 버전
SUPPORTED_EVIDENCE_VERSIONS = ["v1.0", "v1.1"]

# 지원되는 Pattern Library 스키마 버전
SUPPORTED_PATTERN_VERSIONS = ["v1.0"]

# 스키마 타입별 지원 버전 맵
SCHEMA_VERSION_MAP = {
    "vdg": SUPPORTED_VDG_VERSIONS,
    "evidence": SUPPORTED_EVIDENCE_VERSIONS,
    "pattern": SUPPORTED_PATTERN_VERSIONS,
}


def validate_schema_version(
    schema: Dict[str, Any],
    context: str = "",
    schema_type: str = "vdg",
    raise_on_missing: bool = True,
) -> Optional[str]:
    """
    스키마 버전 검증
    
    Args:
        schema: 검증할 스키마 딕셔너리
        context: 오류 메시지에 포함할 컨텍스트 (예: "gemini_analysis", "outlier_ingest")
        schema_type: 스키마 유형 ("vdg", "evidence", "pattern")
        raise_on_missing: True면 버전 없을 때 예외, False면 None 반환
        
    Returns:
        검증된 스키마 버전 문자열
        
    Raises:
        SchemaValidationError: 버전이 없거나 지원되지 않는 경우
    """
    if not isinstance(schema, dict):
        raise SchemaValidationError(
            f"Schema must be a dict, got {type(schema).__name__}",
            context=context
        )
    
    # 버전 필드 추출 (여러 형식 지원)
    version = schema.get("schema_version") or schema.get("version") or schema.get("spec_version")
    
    if not version:
        if raise_on_missing:
            raise SchemaValidationError(
                f"Missing schema_version in {context or 'schema'}",
                context=context
            )
        return None
    
    # 지원 버전 확인
    supported_versions = SCHEMA_VERSION_MAP.get(schema_type, SUPPORTED_VDG_VERSIONS)
    
    if version not in supported_versions:
        raise SchemaValidationError(
            f"Unsupported schema version '{version}' in {context or 'schema'}. "
            f"Supported: {supported_versions}",
            context=context,
            schema_version=version
        )
    
    logger.debug(f"Schema version validated: {version} in {context}")
    return version


def validate_required_fields(
    data: Dict[str, Any],
    required_fields: List[str],
    context: str = "",
) -> None:
    """
    필수 필드 검증
    
    Args:
        data: 검증할 데이터
        required_fields: 필수 필드 목록
        context: 오류 메시지 컨텍스트
        
    Raises:
        SchemaValidationError: 필수 필드 누락 시
    """
    missing = [f for f in required_fields if f not in data or data[f] is None]
    
    if missing:
        raise SchemaValidationError(
            f"Missing required fields in {context or 'data'}: {missing}",
            context=context
        )


def validate_outlier_schema(data: Dict[str, Any]) -> None:
    """
    Outlier 데이터 스키마 검증
    
    필수 필드:
    - platform
    - external_id 또는 video_url
    """
    required = ["platform"]
    validate_required_fields(data, required, context="outlier")
    
    # external_id 또는 video_url 중 하나는 필수
    if not data.get("external_id") and not data.get("video_url"):
        raise SchemaValidationError(
            "Outlier must have either 'external_id' or 'video_url'",
            context="outlier"
        )
    
    # platform 값 검증
    valid_platforms = ["tiktok", "youtube", "instagram", "virlo", "twitter", "x"]
    platform = (data.get("platform") or "").lower()
    if platform and platform not in valid_platforms:
        logger.warning(f"Unknown platform: {platform}")


def validate_vdg_analysis_schema(schema: Dict[str, Any]) -> str:
    """
    VDG 분석 스키마 검증 (Gemini 출력)
    
    필수 구조:
    - hook_genome 또는 intent_layer
    - microbeat_sequence (권장)
    """
    version = validate_schema_version(schema, context="vdg_analysis", schema_type="vdg")
    
    # 핵심 구조 확인
    has_hook_genome = "hook_genome" in schema
    has_intent_layer = "intent_layer" in schema
    
    # Check for microbeats in correct location: hook_genome.microbeats
    hook_genome = schema.get("hook_genome") or {}
    has_microbeats = bool(hook_genome.get("microbeats"))
    
    if not has_hook_genome and not has_intent_layer:
        raise SchemaValidationError(
            "VDG analysis must have 'hook_genome' or 'intent_layer'",
            context="vdg_analysis",
            schema_version=version
        )
    
    if not has_microbeats:
        logger.warning("VDG analysis missing 'hook_genome.microbeats' - clustering quality may be reduced")
    
    return version


def validate_pattern_library_schema(data: Dict[str, Any]) -> str:
    """
    Pattern Library 스키마 검증
    
    필수 필드:
    - pattern_id
    - cluster_id
    - invariant_rules
    - mutation_strategy
    """
    required = ["pattern_id", "cluster_id", "invariant_rules", "mutation_strategy"]
    validate_required_fields(data, required, context="pattern_library")
    
    # invariant_rules 구조 검증
    rules = data.get("invariant_rules")
    if not isinstance(rules, dict):
        raise SchemaValidationError(
            "invariant_rules must be a dict",
            context="pattern_library"
        )
    
    # mutation_strategy 구조 검증
    strategy = data.get("mutation_strategy")
    if not isinstance(strategy, dict):
        raise SchemaValidationError(
            "mutation_strategy must be a dict",
            context="pattern_library"
        )
    
    return data.get("schema_version", "v1.0")


def validate_evidence_event_schema(data: Dict[str, Any]) -> None:
    """
    Evidence Event 스키마 검증
    """
    required = ["parent_node_id"]
    validate_required_fields(data, required, context="evidence_event")


def validate_decision_object_schema(data: Dict[str, Any]) -> None:
    """
    Decision Object 스키마 검증
    """
    required = ["decision_type", "decision_json"]
    validate_required_fields(data, required, context="decision_object")
    
    # decision_type 값 검증
    valid_types = ["go", "stop", "pivot", "GO", "STOP", "PIVOT"]
    if data.get("decision_type") not in valid_types:
        raise SchemaValidationError(
            f"Invalid decision_type: {data.get('decision_type')}. Valid: go, stop, pivot",
            context="decision_object"
        )
