# Komission MCP 개발 워크플로우
# 사용법: /mcp 명령으로 이 워크플로우를 실행합니다.

---
description: MCP 서버 상태 점검 및 테스트
---

## MCP 개발 워크플로우

### 1. 상태 점검
// turbo
```bash
cd /Users/ted/komission/backend
PYTHONPATH=/Users/ted/komission/backend /Users/ted/komission/backend/venv/bin/python tests/test_mcp_hardening.py
```

### 2. 자동화 테스트 실행
// turbo
```bash
cd /Users/ted/komission/backend
PYTHONPATH=/Users/ted/komission/backend /Users/ted/komission/backend/venv/bin/pytest tests/test_mcp_integration.py -v --tb=short
```

### 3. MCP 서버 재시작
```bash
cd /Users/ted/komission/backend
python -m app.mcp_server
```

### 4. HTTP 서버 단독 실행 (선택)
```bash
cd /Users/ted/komission/backend
python -m app.mcp.http_server
```

## MCP 구성 요약

| 구분 | 개수 | 위치 |
|------|------|------|
| Resources | 6개 | `app/mcp/resources/` |
| Tools | 5개 | `app/mcp/tools/` |
| Prompts | 3개 | `app/mcp/prompts/` |

## 도구 목록

| 도구 | 설명 |
|------|------|
| `search_patterns` | 패턴 검색 |
| `generate_source_pack` | NotebookLM 소스팩 |
| `reanalyze_vdg` | VDG 재분석 |
| `smart_pattern_analysis` | AI 패턴 분석 (LLM Sampling) |
| `ai_batch_analysis` | AI 배치 트렌드 분석 |

## 테스트 파일

- **하드닝 테스트**: `tests/test_mcp_hardening.py` (수동 실행용)
- **통합 테스트**: `tests/test_mcp_integration.py` (pytest, CI 자동)

## 에러 발생 시 체크리스트

1. **Import 실패**: `app/mcp/__init__.py` 확인
2. **도구 미등록**: 각 도구 모듈의 `@mcp.tool()` 데코레이터 확인
3. **FastAPI 마운트 실패**: `app/main.py`의 `app.mount("/mcp", ...)` 확인
4. **Pydantic 에러**: `app/mcp/schemas/` 스키마 정의 확인
