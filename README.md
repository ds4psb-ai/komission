# K-MEME FACTORY v5.2

> **바이럴 밈 레시피 플랫폼** - Hybrid Intelligence MVP

AI 분석 + 크리에이터 가이드 + K-Success 인증

---

## 🚀 Quick Start

### 1. 인프라 시작 (Docker)
```bash
docker-compose up -d
```

### 2. 백엔드 실행
```bash
cd backend
python3.13 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 3. 프론트엔드 실행
```bash
cd frontend
bun install
bun run dev
```

### 4. 접속
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Neo4j Browser**: http://localhost:7474

---

## 📁 프로젝트 구조

```
kmeme/
├── backend/                 # FastAPI 백엔드
│   ├── app/
│   │   ├── main.py         # 앱 엔트리포인트
│   │   ├── config.py       # 설정
│   │   ├── database.py     # 비동기 PostgreSQL
│   │   ├── models.py       # SQLAlchemy 모델
│   │   ├── routers/        # API 라우터
│   │   ├── services/       # 비즈니스 로직
│   │   ├── repositories/   # 데이터 접근 계층
│   │   └── middleware/     # 보안 미들웨어
│   └── requirements.txt
│
├── frontend/                # Next.js 프론트엔드
│   └── src/
│       ├── app/            # App Router 페이지
│       └── lib/            # API 클라이언트
│
├── docker-compose.yml       # PostgreSQL + Neo4j + Redis
└── docs/                    # 설계 문서
```

---

## 🔧 기술 스택

| 분류 | 기술 |
|-----|------|
| **AI** | Gemini 3.0 Pro, Claude 4.5 Opus |
| **Backend** | Python 3.13, FastAPI, SQLAlchemy 2.0, asyncpg |
| **Frontend** | Next.js 16, React 19, TypeScript 5.9, TailwindCSS 4.1 |
| **Database** | PostgreSQL 16 (PostGIS, pgvector), Neo4j 5.15, Redis 7 |
| **Auth** | JWT (PyJWT) |

---

## 📚 API 엔드포인트

### 인증
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/v1/auth/token` | JWT 로그인 |
| GET | `/api/v1/auth/me` | 현재 사용자 정보 |

### 리믹스
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/v1/remix/` | 노드 목록 |
| GET | `/api/v1/remix/{node_id}` | 노드 상세 |
| POST | `/api/v1/remix/` | 노드 생성 (Admin) |
| POST | `/api/v1/remix/{node_id}/analyze` | Gemini 분석 실행 |
| POST | `/api/v1/remix/{node_id}/fork` | 노드 Fork |
| PATCH | `/api/v1/remix/{node_id}/publish` | 노드 발행 |

---

## 📖 문서

- [비즈니스 로직 설계서](./K-MEME%20FACTORY%20v5.2%20-%20Hybrid%20Intelligence%20MVP.md)
- [기술 운영 설계서](./K-MEME-v5.2-OPERATIONS.md)

---

## 🛠️ 개발 상태

### ✅ 완료
- 비동기 PostgreSQL 연결 (asyncpg)
- 보안 헤더 미들웨어 (HSTS, CSP, X-Frame-Options)
- JWT 인증
- Repository Pattern
- SQLAlchemy 모델 (User, RemixNode, UserVideo, O2OLocation)
- API 라우터 (Auth, Remix CRUD)
- 프론트엔드 홈/목록/상세 페이지

### 🚧 진행 중
- Rate Limiting 적용
- Redis 캐싱 구현
- 테스트 작성

### 📅 향후 계획
- Neo4j Genealogy Graph
- O2O 위치 인증
- Sentry/Datadog 연동

---

**Version**: 5.2 | **License**: MIT
