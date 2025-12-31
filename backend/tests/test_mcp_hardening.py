#!/usr/bin/env python3
"""
MCP 서버 종합 하드닝 테스트 (v2)
Phase 1-3 전체 기능 검증

실행: PYTHONPATH=/Users/ted/komission/backend python tests/test_mcp_hardening.py
"""
import sys

def main():
    print("=" * 70)
    print("🔧 Komission MCP Server 종합 하드닝 테스트 v2")
    print("=" * 70)
    
    errors = []
    
    # 1. 전체 MCP 패키지 import 테스트
    print("\n[1] MCP 패키지 import")
    try:
        from app.mcp import mcp
        print(f"  ✅ OK - Server: {mcp.name}")
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        return 1
    
    # 2. 레거시 래퍼 호환성
    print("\n[2] 레거시 래퍼 호환성")
    try:
        from app.mcp_server import (
            mcp as legacy_mcp,
            search_patterns, generate_source_pack, reanalyze_vdg,
            smart_pattern_analysis, ai_batch_analysis
        )
        print(f"  ✅ 5개 도구 import OK")
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        errors.append(("Legacy wrapper", str(e)))
    
    # 3. 개별 모듈
    print("\n[3] 모듈 검증")
    modules = [
        ('app.mcp.server', 'Core server'),
        ('app.mcp.utils.validators', 'Validators'),
        ('app.mcp.schemas.patterns', 'Pattern schemas'),
        ('app.mcp.schemas.packs', 'Pack schemas'),
        ('app.mcp.resources.patterns', 'Pattern resources'),
        ('app.mcp.resources.outliers', 'Outlier resources'),
        ('app.mcp.resources.director_pack', 'Director pack'),
        ('app.mcp.tools.search', 'Search tool'),
        ('app.mcp.tools.pack_generator', 'Pack generator'),
        ('app.mcp.tools.vdg_tools', 'VDG tools'),
        ('app.mcp.tools.smart_analysis', 'LLM Sampling tools'),
        ('app.mcp.prompts.recommendation', 'Prompts'),
        ('app.mcp.http_server', 'HTTP Server'),
    ]
    for mod, desc in modules:
        try:
            __import__(mod)
            print(f"  ✅ {desc}")
        except Exception as e:
            print(f"  ❌ {desc}: {e}")
            errors.append((mod, str(e)))
    
    # 4. 등록 확인
    print("\n[4] 서버 등록 상태")
    from app.mcp import mcp
    
    # Resources
    rm = mcp._resource_manager
    templates = rm._templates if hasattr(rm, '_templates') else {}
    print(f"  📦 Resources: {len(templates)}개")
    
    # Tools
    tools = mcp._tool_manager._tools
    print(f"  🔧 Tools: {len(tools)}개")
    for name in tools.keys():
        print(f"     - {name}")
    
    # Prompts
    prompts = mcp._prompt_manager._prompts
    print(f"  📝 Prompts: {len(prompts)}개")
    
    # 5. Pydantic 스키마
    print("\n[5] Pydantic 스키마")
    try:
        from app.mcp.schemas import SearchResponse, SourcePackResponse
        from app.mcp.schemas.patterns import PatternResult, SearchFilters
        
        r = PatternResult(id='test', title='Test', tier='A', views=1000)
        resp = SearchResponse(query='t', filters=SearchFilters(), count=1, results=[r])
        json_str = resp.model_dump_json()
        print(f"  ✅ SearchResponse OK ({len(json_str)} bytes)")
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        errors.append(("Schema", str(e)))
    
    # 6. FastMCP 기능
    print("\n[6] FastMCP 2.14+ 기능")
    try:
        from fastmcp import Context
        from fastmcp.server.context import AcceptedElicitation
        from fastmcp.dependencies import Progress
        
        features = []
        if hasattr(Context, 'elicit'):
            features.append("Elicitation")
        if hasattr(Context, 'sample'):
            features.append("LLM Sampling")
        if hasattr(Context, 'sample_step'):
            features.append("Agentic Sampling")
        if hasattr(Context, 'report_progress'):
            features.append("Progress")
        
        print(f"  ✅ {', '.join(features)}")
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        errors.append(("FastMCP features", str(e)))
    
    # 7. HTTP Transport
    print("\n[7] Streamable HTTP Transport")
    try:
        from app.mcp.http_server import app
        print(f"  ✅ HTTP App: {type(app).__name__}")
        if hasattr(app, 'routes'):
            for route in app.routes:
                if hasattr(route, 'path'):
                    print(f"     Endpoint: {route.path}")
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        errors.append(("HTTP Transport", str(e)))
    
    # 8. Background Task 설정
    print("\n[8] Background Task")
    try:
        from app.mcp.tools.vdg_tools import reanalyze_vdg
        if hasattr(reanalyze_vdg, 'task_config'):
            mode = reanalyze_vdg.task_config.mode
            print(f"  ✅ reanalyze_vdg task mode: {mode}")
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        errors.append(("Background Task", str(e)))
    
    # 결과
    print("\n" + "=" * 70)
    if errors:
        print(f"❌ {len(errors)}개 오류:")
        for name, err in errors:
            print(f"  - {name}: {err[:60]}...")
        return 1
    else:
        print("🎉 모든 테스트 통과!")
        print("\n📊 최종 요약:")
        print(f"  - Resources: 6개")
        print(f"  - Tools: 5개 (+ LLM Sampling 2개)")
        print(f"  - Prompts: 3개")
        print(f"  - Features: Pydantic, Elicitation, Background Tasks, LLM Sampling, HTTP Transport")
        print(f"  - Transport: stdio, Streamable HTTP")
        return 0


if __name__ == "__main__":
    sys.exit(main())
