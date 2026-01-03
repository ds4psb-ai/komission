# Komission MCP Server - Claude Desktop 연동 가이드

**Updated**: 2026-01-04 (v3)  
**MCP Spec**: 2025-11-25 | **FastMCP**: 2.14+ | **AAIF**: 2025-12-09

> [!NOTE]
> 2025-12-09: MCP가 **Agentic AI Foundation (AAIF)**에 기증됨 (Linux Foundation 산하)
> 공동 창립: Anthropic, OpenAI, Block | 지원: Google, Microsoft, AWS

---

## 1. 사전 요구사항

- Claude Desktop 앱 설치
- Python 3.12+ 환경
- Komission 백엔드 가상환경(venv) 활성화

---

## 2. Claude Desktop 설정

### 2.1 설정 파일 위치
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

### 2.2 설정 방법 (GUI)
1. Claude Desktop 실행
2. 메뉴: **Claude → Settings**
3. **Developer** 탭 선택
4. **Edit Config** 클릭

### 2.3 설정 내용

아래 내용을 `claude_desktop_config.json`에 추가/병합:

```json
{
  "mcpServers": {
    "komission": {
      "command": "/Users/ted/komission/backend/venv/bin/python",
      "args": ["-m", "app.mcp_server"],
      "cwd": "/Users/ted/komission/backend",
      "env": {
        "PYTHONPATH": "/Users/ted/komission/backend"
      }
    }
  }
}
```

> ⚠️ venv 경로가 다르면 `command`를 본인 환경에 맞게 변경
> ⚠️ 기존 설정이 있다면 `mcpServers` 객체에 `komission` 항목만 추가

### 2.4 적용
Claude Desktop 완전히 종료 후 재시작

---

## 3. 사용 가능한 리소스 (Resources)

읽기 전용 데이터 조회:

| URI | 설명 |
|-----|------|
| `komission://patterns/{cluster_id}` | 패턴 라이브러리 (클러스터 정보) |
| `komission://comments/{outlier_id}` | 베스트 댓글 5개 (좋아요 정렬) |
| `komission://evidence/{pattern_id}` | Evidence 요약 (댓글+신호+지표) |
| `komission://recurrence/{cluster_id}` | 재등장 lineage (배치 계산 결과) |
| `komission://vdg/{outlier_id}` | VDG 분석 결과 (품질 스코어) |
| `komission://director-pack/{outlier_id}` | Director Pack (VDG v4 기반, on-demand 생성) |
| `stpf://patterns/{pattern_id}` | STPF v3.1 패턴 평가 (읽기 전용) |
| `stpf://grades` | STPF 등급 기준표 (읽기 전용) |
| `stpf://health` | STPF 시스템 상태 (읽기 전용) |
| `stpf://variables` | STPF 변수 정의/범위 (읽기 전용) |

---

## 4. 사용 가능한 도구 (Tools)

| Tool | 용도 | 승인 필요 |
|------|------|----------|
| `search_patterns` | L1/L2 패턴 검색 | 자동 승인 |
| `generate_source_pack` | NotebookLM 소스팩 생성 | **명시적 동의** |
| `reanalyze_vdg` | VDG 재분석 요청 (비용 발생) | **명시적 동의** |
| `smart_pattern_analysis` | 패턴 데이터 제공 (Claude 분석용) | 자동 승인 |
| `ai_batch_analysis` | 배치 데이터 제공 (Claude 비교용) | 자동 승인 |
| `get_pattern_performance` | 성과 데이터 제공 | 자동 승인 |
| `stpf_full_analyze` | STPF 16변수 정밀 분석 | 자동 승인 |
| `stpf_quick_score` | STPF 5변수 빠른 점수 | 자동 승인 |
| `stpf_compare_content` | STPF A/B 비교 | 자동 승인 |
| `stpf_simulate_scenarios` | STPF ToT 시뮬레이션 | 자동 승인 |
| `stpf_monte_carlo` | STPF 몬테카를로 | 자동 승인 |
| `stpf_kelly_decision` | Kelly 의사결정 | 자동 승인 |
| `stpf_get_anchor` | STPF 앵커 해석 | 자동 승인 |

### 4.1 search_patterns
```python
search_patterns(
    query: str,           # 검색 키워드
    category: str = None, # beauty, food, tech 등
    platform: str = None, # tiktok, shorts, reels
    min_tier: str = "C",  # 최소 티어 (S/A/B/C)
    limit: int = 10,      # 최대 결과 수 (max 50)
    output_format: str = "markdown" # markdown | json
)
```

### 4.2 generate_source_pack
```python
generate_source_pack(
    outlier_ids: list[str],    # UUID 목록
    pack_name: str,            # 팩 이름
    include_comments: bool = True,
    include_vdg: bool = True,
    output_format: str = "markdown" # markdown | json
)
```

### 4.3 reanalyze_vdg
```python
reanalyze_vdg(
    outlier_id: str,   # 분석할 outlier UUID
    force: bool = False # 완료된 것도 재분석
)
```

### 4.4 smart_pattern_analysis (데이터 제공)
```python
smart_pattern_analysis(
    outlier_id: str,           # 분석할 outlier UUID
    analysis_type: str = "full"  # full | basic | vdg_only
)
```
> 구조화된 패턴 데이터를 반환합니다. Claude가 이 데이터를 받아서 자체 분석합니다.  
> **서버 비용 $0** - Claude의 토큰으로 분석.

### 4.5 ai_batch_analysis (배치 데이터 제공)
```python
ai_batch_analysis(
    outlier_ids: list[str],    # UUID 목록 (2-10개)
    focus: str = "comparison"  # comparison | trends | strategy
)
```
> 여러 패턴의 비교 데이터를 반환합니다. Claude가 트렌드와 공통점을 분석합니다.

### 4.6 get_pattern_performance (성과 데이터)
```python
get_pattern_performance(
    outlier_id: str,    # outlier UUID
    period: str = "30d" # 7d | 30d | 90d
)
```
> 성과 지표 테이블을 반환합니다. Claude가 성과를 평가합니다.

### 4.7 STPF v3.1 도구
STPF 도구는 모두 구조화된 분석 결과를 반환합니다. 점수 해석은 `docs/STPF_V3_ROADMAP.md`를 참고하세요.

---

## 5. 사용 가능한 프롬프트 (Prompts)

| Prompt ID | 용도 |
|-----------|------|
| `explain_recommendation` | 추천 이유 설명 생성 |
| `shooting_guide` | 촬영 가이드 요약 생성 |
| `risk_summary` | 리스크 분석 생성 |

---

## 6. 핵심 사용 패턴 (권장)

### 6.1 Claude가 분석하도록 하기

```
사용자: "이 패턴 분석해줘" (outlier_id 제공)
   ↓
Claude: smart_pattern_analysis 도구 호출
   ↓
서버: 구조화된 데이터 반환 (조회수, 성장률, VDG 등)
   ↓
Claude: 데이터를 보고 자체 분석 (서버 비용 $0)
   ↓
사용자: AI 분석 결과 확인
```

**예시 대화:**
```
사용자: "Komission에서 이 패턴이 왜 성공했는지 분석해줘"
Claude: [도구 호출: smart_pattern_analysis]
Claude: "조회수 10만, 성장률 1300%로 S-Tier입니다. 성공 요인은..."
```

### 6.2 여러 패턴 비교

```
사용자: "이 3개 패턴 비교해줘"
Claude: [도구 호출: ai_batch_analysis]
Claude: "3개 패턴의 공통점은..."
```

---

## 7. 테스트

### 6.1 독립 실행 테스트
```bash
cd /Users/ted/komission/backend
source venv/bin/activate
python -m app.mcp_server
```

### 6.2 Claude Desktop에서 테스트
Claude와 대화 중:
```
Komission에서 beauty 카테고리 패턴을 검색해줘
```

---

## 7. 문제 해결

### 서버 연결 안됨
1. Claude Desktop 완전 종료 (Cmd+Q)
2. 설정 파일 JSON 문법 확인
3. Python 경로 확인: `which python`
4. 재시작

### 리소스 조회 에러
1. DB 연결 상태 확인
2. `.env`가 로딩되는지 확인 (cwd가 backend인지)
3. outlier_id는 UUID, cluster_id는 문자열 형식 확인

---

## 8. MCP vs Audio Coaching 관계

> [!IMPORTANT]
> **Audio Coaching에 MCP는 필요 없습니다**
> 
> 현재 `audio_coach.py`는 Gemini 2.5 Flash Native Audio를 WebSocket으로 직접 호출합니다.
> 이 아키텍처가 실시간 음성 코칭에 최적입니다.

| 구분 | MCP | Gemini Native Audio |
|------|-----|---------------------|
| 용도 | 도구/데이터 연결 | 실시간 음성 처리 |
| 프로토콜 | HTTP/SSE | WebSocket |
| 오디오 스트리밍 | ❌ 미지원 | ✅ 네이티브 |
| Audio Coaching 적합성 | ❌ | ✅ |

### MCP 활용 가능 영역 (Audio Coaching 아닌)
- `komission://director-pack/{outlier_id}` - Director Pack 조회 (VDG v4 기반, 선택적)

---

## 9. Reference

- MCP 서버 코드: `backend/app/mcp_server.py` (922줄)
- Audio Coach: `backend/app/services/audio_coach.py` (842줄)
- FastMCP 문서: https://gofastmcp.com
- MCP 2025-11-25 스펙: https://modelcontextprotocol.io

---

## 10. FastMCP 2.14+ 가이드 (2025-11-25 스펙)

### 10.1 주요 신기능

| 기능 | 설명 | 상태 |
|------|------|------|
| **Background Tasks** | `task=True` 데코레이터로 장기 작업 진행률 보고 | ✅ 적용 |
| **Progress 의존성** | `Progress` 의존성 주입으로 진행률 추적 | ✅ 적용 |
| **Elicitation** | 서버가 사용자에게 추가 입력 요청 | ✅ 적용 |
| **Server Composition** | 여러 MCP 서버 모듈 조합 | 향후 고려 |
| **Structured Output** | Pydantic 모델 반환 (`SearchResponse`, `SourcePackResponse`) | ✅ 적용 |

### 10.2 Background Task + Progress 패턴 (적용됨)

```python
from fastmcp.dependencies import Progress

@mcp.tool(task=True)  # Background Task 활성화
async def reanalyze_vdg(
    outlier_id: str,
    force: bool = False,
    progress: Progress = Progress()  # 의존성 주입
) -> str:
    await progress.set_total(4)
    await progress.set_message("Validating outlier ID")
    # ... 검증 로직
    await progress.increment()
    
    await progress.set_message("Queuing for re-analysis")
    # ... 큐 등록
    await progress.increment()
    return result
```

### 10.3 Elicitation (적용됨)

서버가 도구 실행 중 사용자에게 추가 정보를 요청하는 MCP 2025-06-18 신기능:

**적용된 도구**:
- `generate_source_pack`: 20개 초과 선택 시 확인 요청
- `reanalyze_vdg`: `force=True` 시 비용 확인 요청

```python
from fastmcp import Context
from fastmcp.server.context import AcceptedElicitation

ELICITATION_THRESHOLD = 20

@mcp.tool()
async def generate_source_pack(
    outlier_ids: list[str],
    pack_name: str,
    ctx: Context = None
):
    if len(outlier_ids) > ELICITATION_THRESHOLD and ctx:
        response = await ctx.elicit(
            message=f"⚠️ {len(outlier_ids)}개의 아웃라이어가 선택되었습니다. 계속하시겠습니까?",
            response_type=bool
        )
        
        if not isinstance(response, AcceptedElicitation) or not response.data:
            return "❌ 작업이 취소되었습니다."
```

### 10.4 Transport Layer

| Transport | 사용 케이스 | 설정 |
|-----------|------------|------|
| **stdio** | Claude Desktop 로컬 연동 (현재) | `mcp.run()` |
| **Streamable HTTP** | 원격 MCP 서버 | `python -m app.mcp.http_server` |

#### Streamable HTTP 실행

```bash
# 개발 모드
cd backend
python -m app.mcp.http_server

# Docker 배포
docker-compose -f docker-compose.mcp.yml up -d
```

#### 클라이언트 연결 (원격)

```json
{
  "mcpServers": {
    "komission": {
      "transport": "http",
      "url": "https://api.komission.io/mcp"
    }
  }
}
```

> ⚠️ SSE(Server-Sent Events)는 2025-03-26 스펙에서 deprecated됨

### 10.5 2025 Best Practices

1. **Background Tasks**: `task=True` + `Progress` 의존성 주입
2. **보안**: OAuth 2.1 + PKCE (원격 배포 시 필수)
3. **입력 검증**: Pydantic strict validation
4. **비동기**: `async` 도구 선언 필수
5. **모듈화**: 도메인별 마이크로 서버 분리
6. **에러 처리**: JSON-RPC 2.0 에러 코드 사용

---

## 11. 2025-12 신규 스펙 (향후 적용)

### 11.1 MCP Apps Extension (SEP-1865)

2025-11 OpenAI + Anthropic + MCP-UI 협력으로 표준화된 UI 위젯:

| 구성요소 | 패키지 |
|----------|--------|
| 서버 어댑터 | `@mcp-ui/server` |
| ChatGPT 통합 | OpenAI Apps SDK |
| Claude 통합 | 네이티브 MCP |

**적용 예정:** 에이전트 채팅 Hub-Spokes UI 위젯

### 11.2 Tasks Primitive (2025-11)

Background Tasks 대신 공식 `Tasks` primitive로 비동기 장기 작업:

```python
# 현재: Background Tasks
@mcp.tool(task=True)
async def long_running_task(...): ...

# 향후: Tasks Primitive (마이그레이션 고려)
@mcp.task()
async def long_running_task(...): ...
```

### 11.3 OAuth 2.1 CIMD

Client ID Metadata Documents로 Dynamic Client Registration 대체:

```json
// .well-known/oauth-client-metadata.json
{
  "client_id": "komission-mcp-server",
  "redirect_uris": ["https://api.komission.io/oauth/callback"],
  "grant_types": ["authorization_code", "refresh_token"],
  "scope": "read write"
}
```

**적용 시점:** 엔터프라이즈 배포 시

---

## 12. Reference

- MCP 서버 코드: `backend/app/mcp/` (모듈화됨)
- MCP 공식 스펙: https://modelcontextprotocol.io
- AAIF: https://agenticaifoundation.org (Linux Foundation)
- FastMCP 문서: https://gofastmcp.com
- MCP-UI: https://mcpui.dev

