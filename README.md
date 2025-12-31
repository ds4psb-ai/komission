# Komission | 바이럴 콘텐츠 인텔리전스 플랫폼

> **Viral Depth Genealogy + Evidence Loop** 기반 숏폼 리믹스 실험 플랫폼

## 🚀 주요 기능

| 기능 | 설명 |
| --- | --- |
| **Outlier 수집** | 바이럴 영상 발굴 및 VDG 분석 |
| **Evidence Loop** | 증거 기반 의사결정 시스템 |
| **Canvas** | 노드 기반 템플릿 시스템 |
| **O2O 캠페인** | 제품 체험단 운영 |
| **Analytics** | KPI 대시보드 및 리포트 |

## 📐 아키텍처

```
Outlier 수집 → Gemini 분석 → VDG 클러스터링
    ↓
Parent 승격 → Depth 실험 → Evidence/Decision
    ↓
Capsule 실행 → O2O 연결 → 성과 측정
```

**핵심 원칙:**
- **DB = SoR** (System of Record)
- **Sheets = Ops/Share Bus**
- **NotebookLM/Opal = DB-wrapped accelerators**

## 🛠️ 기술 스택

| 구분 | 기술 |
| --- | --- |
| **Backend** | Python 3.12+, FastAPI, SQLAlchemy |
| **Frontend** | Next.js 16, React 19, Tailwind CSS |
| **DB** | PostgreSQL, Redis, Neo4j |
| **AI** | Gemini 2.0 Pro |
| **Auth** | Firebase Auth |

## ⚡ Quick Start

```bash
# 백엔드
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 프론트엔드
cd frontend
bun install && bun run dev
```

## 📚 API 문서

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🧪 테스트

```bash
# E2E 테스트
cd frontend
npm run test:e2e

# 린트
npm run lint
```

## 📁 프로젝트 구조

```
komission/
├── backend/
│   ├── app/
│   │   ├── routers/      # API 엔드포인트
│   │   ├── services/     # 비즈니스 로직
│   │   ├── models/       # DB 모델
│   │   └── schemas/      # Pydantic 스키마
│   └── scripts/          # 운영 스크립트
│
├── frontend/
│   ├── src/
│   │   ├── app/          # Next.js 페이지
│   │   ├── components/   # UI 컴포넌트
│   │   ├── lib/          # 유틸리티
│   │   └── hooks/        # React 훅
│   └── e2e/              # E2E 테스트
│
└── docs/                 # 문서
```

## 📖 문서 목록

| 문서 | 설명 |
| --- | --- |
| [00_EXECUTIVE_SUMMARY](docs/00_EXECUTIVE_SUMMARY.md) | 요약 |
| [01_VDG_SYSTEM](docs/01_VDG_SYSTEM.md) | VDG 시스템 |
| [03_IMPLEMENTATION_ROADMAP](docs/03_IMPLEMENTATION_ROADMAP.md) | 로드맵 |
| [15_FINAL_ARCHITECTURE](docs/15_FINAL_ARCHITECTURE.md) | 최종 아키텍처 |
| [16_PDR](docs/16_PDR.md) | 제품 요구사항 |

## 📊 KPI

| 지표 | 목표 |
| --- | --- |
| Evidence 생성 시간 | < 24시간 |
| 템플릿 완료율 | > 60% |
| Pattern Lift | > 2x |

---

**© 2025 Komission. All rights reserved.**
