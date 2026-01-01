#!/usr/bin/env python3
"""
Proof-Grade VDG Test Script
사용자 수동 테스트용

실행 방법:
cd /Users/ted/komission/backend
source venv/bin/activate
python scripts/test_proof_grade_vdg.py
"""

import asyncio
import json
from dotenv import load_dotenv
load_dotenv('.env')


async def test_proof_grade_vdg():
    from app.services.gemini_pipeline import gemini_pipeline
    
    # 테스트 영상
    url = 'https://www.youtube.com/shorts/FjTVH7gIIi0'
    
    # 20개 댓글 시뮬레이션 (실제 테스트 시 실제 댓글 사용)
    comments = [
        {'text': '이거 진짜 대박이다 ㅋㅋㅋ', 'likes': 500},
        {'text': '처음 몇초가 미쳤어', 'likes': 450},
        {'text': 'ASMR 느낌 쩐다', 'likes': 400},
        {'text': '이 요리 따라해보고 싶다', 'likes': 350},
        {'text': '마지막 완성샷 예술', 'likes': 300},
        {'text': '와 진짜 맛있겠다', 'likes': 250},
        {'text': '편집 너무 잘했음', 'likes': 200},
        {'text': '이 영상 계속 보게 됨', 'likes': 180},
        {'text': '화질 미쳤다', 'likes': 160},
        {'text': '배경음악 뭐예요?', 'likes': 140},
        {'text': '진짜 프로 셰프인듯', 'likes': 120},
        {'text': '레시피 알려주세요', 'likes': 100},
        {'text': '이런 영상 더 올려주세요', 'likes': 90},
        {'text': '저녁 뭐먹지 고민 끝', 'likes': 80},
        {'text': '손이 너무 예뻐요', 'likes': 70},
        {'text': '칼질 소리 좋다', 'likes': 60},
        {'text': '배고파지네', 'likes': 50},
        {'text': '팔로우했어요!', 'likes': 40},
        {'text': '영상 길이 딱 좋음', 'likes': 30},
        {'text': '다음엔 뭐 만들어주세요?', 'likes': 20},
    ]
    
    print("=" * 60)
    print("🔬 Proof-Grade VDG Test Starting...")
    print("=" * 60)
    
    result = await gemini_pipeline.analyze_video_v4(
        video_url=url,
        node_id='proof_grade_test',
        audience_comments=comments
    )
    
    print("\n" + "=" * 60)
    print("📊 PROOF-GRADE 검증 체크리스트")
    print("=" * 60)
    
    # 1. Comment Evidence Top 5
    best_comments = result.semantic.audience_reaction.best_comments or []
    print(f"\n1️⃣ comment_evidence_top5 개수: {len(best_comments)} (목표: 5)")
    for i, c in enumerate(best_comments[:5], 1):
        anchor = c.get('anchor_ms', 'N/A')
        print(f"   C{i}: rank={c.get('rank')} anchor_ms={anchor} signal={c.get('signal_type')}")
    
    # 2. Viral Kicks
    viral_kicks = result.provenance.get('viral_kicks', [])
    print(f"\n2️⃣ viral_kicks 개수: {len(viral_kicks)} (목표: 3-5)")
    for kick in viral_kicks[:5]:
        print(f"   Kick {kick.get('kick_index')}: {kick.get('title', 'N/A')[:40]}")
        print(f"      evidence_comment_ranks: {kick.get('evidence_comment_ranks')}")
        keyframes = kick.get('keyframes', [])
        print(f"      keyframes: {len(keyframes)}개", end="")
        if keyframes:
            roles = [kf.get('role') for kf in keyframes]
            print(f" ({', '.join(roles)})")
        else:
            print(" (없음 - 전처리로 생성됨)")
    
    # 3. Analysis Plan Coverage
    points = result.analysis_plan.points or []
    print(f"\n3️⃣ analysis_plan.points 개수: {len(points)} (목표: 6-12)")
    kick_connected = sum(1 for p in points if getattr(p, 'kick_index', None) is not None)
    print(f"   kick_index 연결된 포인트: {kick_connected}개")
    
    # 4. Final Score
    print("\n" + "=" * 60)
    checks = [
        len(best_comments) == 5,
        3 <= len(viral_kicks) <= 5,
        all(kick.get('keyframes') for kick in viral_kicks),
        6 <= len(points) <= 12,
    ]
    score = sum(checks)
    print(f"🏆 PROOF-GRADE SCORE: {score}/4")
    
    if score == 4:
        print("✅ 최고 수준 VDG 달성! 증거 기반 분석 완료.")
    else:
        print("⚠️ 일부 항목 미달. 위 세부 내역 확인 필요.")
    
    print("=" * 60)
    
    # 결과 저장
    with open('/tmp/proof_grade_vdg_result.json', 'w', encoding='utf-8') as f:
        json.dump(result.model_dump(), f, ensure_ascii=False, indent=2, default=str)
    print(f"\n💾 전체 결과 저장: /tmp/proof_grade_vdg_result.json")


if __name__ == "__main__":
    asyncio.run(test_proof_grade_vdg())
