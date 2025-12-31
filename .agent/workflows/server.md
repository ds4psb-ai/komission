---
description: Komission 서버 시작/재시작 (Backend 8000, Frontend 3000)
---
# Komission 서버 재시작

// turbo-all

## 1. Docker 컨테이너 시작 (PostgreSQL, Neo4j, Redis)
```bash
cd /Users/ted/komission && docker compose up -d
```

## 2. 기존 uvicorn 프로세스 종료
```bash
pkill -f "uvicorn app.main:app.*8000" 2>/dev/null || echo "No existing uvicorn process"
```

## 3. 백엔드 서버 시작 (포트 8000)
```bash
cd /Users/ted/komission/backend && source venv/bin/activate && nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > /tmp/komission-backend.log 2>&1 &
```

## 4. 백엔드 서버 확인 (3초 대기 후)
```bash
sleep 3 && curl -s -o /dev/null -w "Backend (8000): HTTP %{http_code}\n" http://localhost:8000/health || echo "Backend: Failed to connect"
```

## 5. 프론트엔드 서버 확인/시작 (포트 3000)
```bash
lsof -i :3000 | grep LISTEN > /dev/null 2>&1 && echo "Frontend already running on 3000" || (cd /Users/ted/komission/frontend && nohup npm run dev > /tmp/komission-frontend.log 2>&1 &)
```

## 6. 전체 상태 확인
```bash
sleep 2 && echo "=== Komission Server Status ===" && curl -s -o /dev/null -w "Backend (8000): HTTP %{http_code}\n" http://localhost:8000/health && curl -s -o /dev/null -w "Frontend (3000): HTTP %{http_code}\n" http://localhost:3000/
```
