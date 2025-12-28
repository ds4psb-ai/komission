# Komission MCP Server - Claude Desktop 연동 가이드

## 1. 사전 요구사항

- Claude Desktop 앱 설치
- Python 3.12+ 환경
- Komission 백엔드 가상환경(venv) 활성화

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

> ⚠️ venv 경로가 다르면 `command`를 본인 환경에 맞게 변경하세요.
> ⚠️ 기존 설정이 있다면 `mcpServers` 객체에 `komission` 항목만 추가

### 2.4 적용
Claude Desktop 완전히 종료 후 재시작

## 3. 사용 가능한 리소스

Claude와 대화 중 아래 리소스 URI 요청 가능:

| URI | 설명 |
|-----|------|
| `komission://patterns/{cluster_id}` | 패턴 라이브러리 |
| `komission://comments/{outlier_id}` | 베스트 댓글 5개 |
| `komission://evidence/{pattern_id}` | Evidence 요약 |
| `komission://recurrence/{cluster_id}` | 재등장 lineage |
| `komission://vdg/{outlier_id}` | VDG 분석 결과 |

## 4. 사용 가능한 프롬프트

| Prompt ID | 용도 |
|-----------|------|
| `explain_recommendation` | 추천 이유 설명 |
| `shooting_guide` | 촬영 가이드 |
| `risk_summary` | 리스크 분석 |

## 5. 테스트

### 5.1 독립 실행 테스트
```bash
cd /Users/ted/komission/backend
source venv/bin/activate
python -m app.mcp_server
```

### 5.2 Claude Desktop에서 테스트
Claude와 대화 중:
```
Komission에서 패턴 정보를 가져와줘
```

## 6. 문제 해결

### 서버 연결 안됨
1. Claude Desktop 완전 종료 (Cmd+Q)
2. 설정 파일 JSON 문법 확인
3. Python 경로 확인: `which python`
4. 재시작

### 리소스 조회 에러
1. DB 연결 상태 확인
2. `.env`가 로딩되는지 확인 (cwd가 backend인지)
3. outlier_id는 UUID, cluster_id는 문자열(예: Hook-2s-TextPunch) 형식 확인
