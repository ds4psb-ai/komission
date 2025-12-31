#!/usr/bin/env python3
"""
Pydantic→TypeScript 자동 변환 스크립트
MCP 스키마를 TypeScript 타입으로 변환

실행:
    python scripts/generate_mcp_types.py

출력:
    frontend/src/types/mcp-generated.ts
"""
import json
import sys
from pathlib import Path
from typing import get_type_hints, get_origin, get_args, Any, Optional, List, Dict

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.mcp.schemas.patterns import PatternResult, SearchFilters, SearchResponse
from app.mcp.schemas.packs import VDGInfo, PackSource, SourcePackResponse


def python_type_to_ts(py_type: Any) -> str:
    """Python 타입을 TypeScript 타입으로 변환"""
    import typing
    
    origin = get_origin(py_type)
    args = get_args(py_type)
    
    # NoneType
    if py_type is type(None):
        return 'null'
    
    # Union (Optional은 Union[X, None])
    if origin is typing.Union:
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1:
            return f'{python_type_to_ts(non_none[0])} | null'
        return ' | '.join(python_type_to_ts(a) for a in args)
    
    # List[X]
    if origin is list:
        inner = args[0] if args else 'any'
        return f'{python_type_to_ts(inner)}[]'
    
    # Dict[K, V]
    if origin is dict:
        if len(args) >= 2:
            return f'Record<{python_type_to_ts(args[0])}, {python_type_to_ts(args[1])}>'
        return 'Record<string, any>'
    
    # 기본 타입
    type_map = {
        str: 'string',
        int: 'number',
        float: 'number',
        bool: 'boolean',
        type(None): 'null',
        Any: 'any',
    }
    
    if py_type in type_map:
        return type_map[py_type]
    
    # Pydantic 모델
    if hasattr(py_type, '__name__'):
        return py_type.__name__
    
    return 'any'


def pydantic_to_ts(model_class) -> str:
    """Pydantic 모델을 TypeScript interface로 변환"""
    import typing
    
    lines = []
    name = model_class.__name__
    
    # Docstring 주석으로 변환
    if model_class.__doc__:
        lines.append(f'/** {model_class.__doc__.strip()} */')
    
    lines.append(f'export interface {name} {{')
    
    # 필드 처리
    for field_name, field_info in model_class.model_fields.items():
        annotation = field_info.annotation
        ts_type = python_type_to_ts(annotation)
        
        # Optional 체크 (Union with None)
        origin = get_origin(annotation)
        args = get_args(annotation)
        is_optional = (
            origin is typing.Union and
            type(None) in args
        )
        
        # 기본값 있으면 optional
        has_default = field_info.default is not None or field_info.default_factory is not None
        
        optional_mark = '?' if is_optional or has_default else ''
        
        lines.append(f'    {field_name}{optional_mark}: {ts_type};')
    
    lines.append('}')
    return '\n'.join(lines)


def generate_all_types() -> str:
    """모든 MCP 스키마를 TypeScript로 변환"""
    models = [
        # patterns.py
        PatternResult,
        SearchFilters,
        SearchResponse,
        # packs.py
        VDGInfo,
        PackSource,
        SourcePackResponse,
    ]
    
    output = [
        '/**',
        ' * MCP Generated Types',
        ' * 자동 생성됨 - 직접 수정하지 마세요',
        f' * Generated: {__import__("datetime").datetime.now().isoformat()[:19]}',
        ' * Source: backend/app/mcp/schemas/',
        ' */',
        '',
        '// ==================',
        '// Pattern Types',
        '// ==================',
        '',
    ]
    
    # patterns
    for model in models[:3]:
        output.append(pydantic_to_ts(model))
        output.append('')
    
    output.extend([
        '// ==================',
        '// Pack Types',
        '// ==================',
        '',
    ])
    
    # packs
    for model in models[3:]:
        output.append(pydantic_to_ts(model))
        output.append('')
    
    # 추가 타입 (수동)
    output.extend([
        '// ==================',
        '// Tool Result Types',
        '// ==================',
        '',
        '/** AI 분석 결과 */',
        'export interface AIAnalysisResult {',
        '    content: string;',
        '    analysisType: "full" | "basic" | "vdg_only";',
        '    outlierId: string;',
        '    tier?: string;',
        '    title?: string;',
        '}',
        '',
        '/** 배치 분석 결과 */',
        'export interface BatchAnalysisResult {',
        '    content: string;',
        '    focus: "trends" | "comparison" | "strategy";',
        '    outlierCount: number;',
        '}',
        '',
        '/** 성과 분석 결과 */',
        'export interface PerformanceResult {',
        '    content: string;',
        '    period: "7d" | "30d" | "90d";',
        '    outlierId: string;',
        '}',
        '',
    ])
    
    return '\n'.join(output)


def main():
    output_path = Path(__file__).parent.parent.parent / 'frontend' / 'src' / 'types' / 'mcp-generated.ts'
    
    # types 디렉토리 생성
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    content = generate_all_types()
    output_path.write_text(content, encoding='utf-8')
    
    print(f'✅ Generated: {output_path}')
    print(f'   Lines: {len(content.splitlines())}')


if __name__ == '__main__':
    main()
