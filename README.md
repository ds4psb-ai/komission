# Komission (K-MEME FACTORY v5.2)

> **바이럴 콘텐츠 인텔리전스 플랫폼** - Remix의 계보를 추적하고, 수익화하는 플랫폼

## 🎯 프로젝트 개요

Komission은 바이럴 숏폼 콘텐츠의 "DNA"를 분석하고, 크리에이터가 성공적인 리믹스를 만들 수 있도록 가이드하는 플랫폼입니다.

### 핵심 가치 제안
1. **Outliers 발견** - AI가 터질 가능성이 높은 바이럴 콘텐츠를 선별
2. **Magic Mode** - URL 하나로 즉시 분석 시작 (복잡한 파이프라인 숨김)
3. **Viral Genealogy** - 리믹스의 가계도를 추적하여 원작자에게 로열티 분배
4. **O2O 체험단** - 오프라인 매장과 연계한 퀘스트 기반 수익화

---

## 🚀 Quick Start

### 1. 인프라 시작 (Docker)
```bash
docker-compose up -d  # PostgreSQL, Neo4j, Redis
```

### 2. 백엔드 실행
```bash
cd backend
python3.9 -m venv venv && source venv/bin/activate
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

## 📱 주요 섹션 (4 Pillars)

| 섹션 | 경로 | 설명 |
|------|------|------|
| **아웃라이어** | `/` | 터질 가능성이 높은 바이럴 콘텐츠 발견 |
| **캔버스** | `/canvas` | 노드 기반 리믹스 파이프라인 편집 (Pro Mode) |
| **마켓** | `/o2o` | O2O 체험단 캠페인 마켓플레이스 |
| **마이** | `/my` | 내 리믹스, 로열티 수익, 계보도 |

### 섹션 간 유기적 연결
```
[아웃라이어] → 카드 클릭 → [리믹스 상세]
                            ↓ 퀘스트 수락 (O2O)
                            ↓ 촬영 시작 (Invisible Fork)
                            → [촬영 가이드] → 싱크 조절 → [마이]
                            ↓ 캔버스 편집 (Pro)
                            → [캔버스] (Master = 🔒 잠금)
```

---

## 🛠️ 기술 스택

| 분류 | 기술 |
|-----|------|
| **AI** | Gemini 2.0 Pro (비디오 분석), Claude (한국화 기획) |
| **Backend** | Python 3.9+, FastAPI, SQLAlchemy 2.0, asyncpg |
| **Frontend** | Next.js 16, React 19, TypeScript, TailwindCSS 4 |
| **Database** | PostgreSQL 16 (PostGIS, pgvector), Neo4j 5.x, Redis 7 |
| **Auth** | Google OAuth + Firebase Auth → JWT |
| **Infra** | Docker, GitHub Actions, Vercel |

---

## 📁 프로젝트 구조

```
komission/
├── backend/                 # FastAPI 백엔드
│   ├── app/
│   │   ├── main.py          # 앱 엔트리포인트
│   │   ├── routers/         # API 라우터 (auth, remix, o2o, royalty, pipelines)
│   │   ├── services/        # Gemini, Claude, Graph, Royalty Engine
│   │   └── repositories/    # 데이터 접근 계층
│   └── requirements.txt
│
├── frontend/                # Next.js 프론트엔드
│   └── src/
│       ├── app/             # App Router 페이지
│       │   ├── page.tsx     # 메인 (Magic Mode + 아웃라이어)
│       │   ├── login/       # 로그인 (3D Tilt UI)
│       │   ├── canvas/      # 캔버스 (ReactFlow)
│       │   ├── remix/[nodeId]/ # 상세 (시네마틱 타임라인)
│       │   ├── o2o/         # O2O 마켓
│       │   └── my/          # 마이페이지 + Royalty
│       └── components/      # FilmingGuide, GenealogyWidget 등
│
├── docker-compose.yml       # PostgreSQL + Neo4j + Redis
└── *.md                     # 문서들
```

---

## ✨ UI/UX 하드닝 (최신 구현)

### 로그인 페이지 (`/login`)
- **3D Tilt Card**: 마우스 움직임에 반응하는 카드
- **Aurora Background**: 살아 움직이는 오로라 그라데이션
- **Dynamic Spotlight**: 마우스를 따라다니는 스포트라이트 효과

### 메인 페이지 (`/`)
- **Magic Input**: 글로우 효과 + 로딩 애니메이션
- **TiltCard Grid**: 스크롤 시 순차 등장 + 3D Tilt
- **Viral Badge**: 성장률 (`+127%`) 실시간 표시

### 리믹스 상세 (`/remix/[nodeId]`)
- **Cinematic Timeline**: 영화 필름 스트립 형태의 씬 구성
- **Mise-en-scène Guide**: 매거진 스타일 촬영 디렉션
- **Quest Gamification**: "⚔️ 퀘스트 수락하고 +500P 받기"
- **Invisible Forking**: 촬영 시작 시 자동으로 Fork 생성 (시도 데이터 추적)

### 캔버스 (`/canvas`)
- **Governance Lock**: Master 노드에 🔒 잠금 표시 + 삭제 불가
- **Viral Badge**: 노드에 성장률 배지 표시

---

## 📊 API 엔드포인트

### 인증
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/v1/auth/google` | Google OAuth 로그인 |
| GET | `/api/v1/auth/me` | 현재 사용자 정보 |

### 리믹스
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/v1/remix/` | 노드 목록 (아웃라이어) |
| GET | `/api/v1/remix/{node_id}` | 노드 상세 |
| POST | `/api/v1/remix/` | 노드 생성 |
| POST | `/api/v1/remix/{node_id}/analyze` | Gemini 분석 실행 |
| POST | `/api/v1/remix/{node_id}/fork` | 노드 Fork |

### O2O
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/v1/o2o/campaigns` | 캠페인 목록 |
| POST | `/api/v1/o2o/campaigns/{id}/apply` | 체험단 신청 |

### Royalty
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/v1/royalty/summary` | 수익 요약 |
| GET | `/api/v1/royalty/history` | 거래 내역 |

---

## 📖 문서

| 문서 | 설명 |
|------|------|
| [비즈니스 로직 설계서](./K-MEME%20FACTORY%20v5.2%20-%20Hybrid%20Intelligence%20MVP.md) | 전체 아키텍처 + 비즈니스 로직 |
| [기술 운영 설계서](./K-MEME-v5.2-OPERATIONS.md) | 보안, 캐싱, 모니터링 |
| [프로덕션 가이드](./K-MEME-v5.2-PRODUCTION-READY.md) | 배포 준비 체크리스트 |

---

## 🔗 GitHub Repository

**https://github.com/ds4psb-ai/komission**

---

**Version**: 5.2 | **License**: MIT | **Last Updated**: 2025-12-22
