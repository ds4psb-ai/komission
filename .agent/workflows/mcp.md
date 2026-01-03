# Komission MCP 점검 워크플로우
---
description: MCP 서버 상태 점검 및 테스트
---

// turbo-all

## 1. MCP 서버 Quick Health Check
```bash
cd /Users/ted/komission/backend && curl -s http://localhost:8000/health | head -3
```

## 2. MCP 구성 확인 (자동 생성)
```bash
cd /Users/ted/komission/backend && cat app/mcp/server.json | head -50
```

## 3. MCP 하드닝 테스트 실행
```bash
cd /Users/ted/komission/backend && PYTHONPATH=. /Users/ted/komission/backend/venv/bin/python tests/test_mcp_hardening.py 2>&1 | tail -20
```

## 4. MCP 통합 테스트 (pytest)
```bash
cd /Users/ted/komission/backend && PYTHONPATH=. /Users/ted/komission/backend/venv/bin/pytest tests/test_mcp_integration.py -v --tb=short 2>&1 | tail -30
```

---

## MCP 구성 요약 (2026-01-03 업데이트)

### Tools (5개)
| 파일 | 도구 |
|------|------|
| `search.py` | 패턴 검색 |
| `pack_generator.py` | NotebookLM 소스팩 생성 |
| `vdg_tools.py` | VDG 재분석 |
| `smart_analysis.py` | AI 패턴 분석 (LLM Sampling) |
| `stpf_tools.py` | STPF 도구 모음 |

### Resources (4개)
| 파일 | 리소스 |
|------|--------|
| `patterns.py` | 패턴 라이브러리 |
| `outliers.py` | 아웃라이어 조회 |
| `director_pack.py` | DirectorPack 조회 |
| `stpf.py` | STPF 리소스 |

### Prompts (3개)
| 파일 | 프롬프트 |
|------|---------|
| `recommendation.py` | 추천 |
| `risk.py` | 리스크 분석 |
| `shooting.py` | 촬영 가이드 |

### 테스트 파일 (7개)
| 파일 | 용도 |
|------|------|
| `test_mcp_hardening.py` | 하드닝 체크 |
| `test_mcp_integration.py` | 통합 테스트 |
| `test_mcp_e2e.py` | E2E 테스트 |
| `test_mcp_audit.py` | 감사 테스트 |
| `test_mcp_server.py` | 서버 테스트 |
| `test_mcp_smart_analysis.py` | 스마트 분석 |
| `test_mcp_tools.py` | 도구 테스트 |

---

## 에러 발생 시 체크리스트

1. **서버 안 켜짐**: `/server` 워크플로우로 서버 시작
2. **Import 실패**: `app/mcp/__init__.py` 확인
3. **도구 미등록**: `@mcp.tool()` 데코레이터 확인
4. **FastAPI 마운트**: `app/main.py`의 `/mcp` 마운트 확인
