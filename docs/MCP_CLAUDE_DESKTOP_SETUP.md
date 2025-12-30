# Komission MCP Server - Claude Desktop 연동 가이드

**Updated**: 2025-12-30

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

---

## 4. 사용 가능한 도구 (Tools)

| Tool | 용도 | 승인 필요 |
|------|------|----------|
| `search_patterns` | L1/L2 패턴 검색 | 자동 승인 |
| `generate_source_pack` | NotebookLM 소스팩 생성 | **명시적 동의** |
| `reanalyze_vdg` | VDG 재분석 요청 (비용 발생) | **명시적 동의** |

### 4.1 search_patterns
```python
search_patterns(
    query: str,           # 검색 키워드
    category: str = None, # beauty, food, tech 등
    platform: str = None, # tiktok, shorts, reels
    min_tier: str = "C",  # 최소 티어 (S/A/B/C)
    limit: int = 10       # 최대 결과 수 (max 50)
)
```

### 4.2 generate_source_pack
```python
generate_source_pack(
    outlier_ids: list[str],    # UUID 목록
    pack_name: str,            # 팩 이름
    include_comments: bool = True,
    include_vdg: bool = True
)
```

### 4.3 reanalyze_vdg
```python
reanalyze_vdg(
    outlier_id: str,   # 분석할 outlier UUID
    force: bool = False # 완료된 것도 재분석
)
```

---

## 5. 사용 가능한 프롬프트 (Prompts)

| Prompt ID | 용도 |
|-----------|------|
| `explain_recommendation` | 추천 이유 설명 생성 |
| `shooting_guide` | 촬영 가이드 요약 생성 |
| `risk_summary` | 리스크 분석 생성 |

---

## 6. 테스트

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
- `komission://pack/{pack_id}` - Director Pack 조회 (선택적)
- `generate_pack` - Pack 생성 도구 (선택적)

---

## 9. Reference

- MCP 서버 코드: `backend/app/mcp_server.py` (786줄)
- Audio Coach: `backend/app/services/audio_coach.py` (842줄)
- FastMCP 문서: https://github.com/jlowin/fastmcp
- MCP 2025-06-18 스펙: https://modelcontextprotocol.io

